    const container = document.getElementById('overlay_map');
    fetch('/isp_overlap.json/?asn1=' + asn1 + '&asn2=' + asn2, { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            // Process the JSON data here
            console.log(data);
            ol.proj.useGeographic();

            // Create the map
            const map = new ol.Map({
                target: container,
                layers: [
                    new ol.layer.Tile({         // Add OpenStreetMap layer
                        source: new ol.source.OSM(),
                        opacity: 0.6            // Adjust opacity for transparency
                    }),
                    new ol.layer.Vector({  // Create the vector layer for ISP markers
                        source: new ol.source.Vector()
                    })
                ],
                view: new ol.View({
                    center: [-96, 38],
                    zoom: 4,
                    enableRotation: false
                })
            });

            // Create marker features
            function createFacilityDot(fac_name, coords, color, city, country_code, state, isp_type, port_capacity) {
                const flippedCoords = [coords[1], coords[0]];
                const feature = new ol.Feature({
                    geometry: new ol.geom.Point(flippedCoords),
                    name: fac_name,
                    city: city,
                    country_code: country_code,
                    state: state,
                    isp_type: isp_type,
                    port_capacity: port_capacity
                });
                feature.setStyle(new ol.style.Style({
                    image: new ol.style.Circle({
                        fill: new ol.style.Fill({ color: color }),
                        radius: 6,
                        stroke: new ol.style.Stroke({ color: 'black', width: 1 })
                    })
                }));
                return feature;
            }
            // Helper Functions
            function median(values) {
                values.sort((a, b) => a - b); // Sort numerically
                const mid = Math.floor(values.length / 2);
                return values.length % 2 !== 0 ? values[mid] : (values[mid - 1] + values[mid]) / 2;
            }
            function sortByAngle(points, center) {
            return points.sort((a, b) => {
                const angleA = Math.atan2(a[1] - center[1], a[0] - center[0]);
                const angleB = Math.atan2(b[1] - center[1], b[0] - center[0]);
                return angleA - angleB;
            });
        }
            function sortPointsForPolygon(ispPopLocationsList) {
                // 1. Extract coordinates
                const longitudes = ispPopLocationsList.map(pair => pair[0]);
                const latitudes = ispPopLocationsList.map(pair => pair[1]);

                // 2. Calculate Center
                const center = [median(longitudes), median(latitudes)];

                // 3. Sort Points Clockwise
                const sortedPoints = sortByAngle(ispPopLocationsList, center);


                return sortedPoints;
            }


            // Create polygon feature
            function createPolygonFeature(locations, color) {
                flippedCoords = locations.map(pair => [pair[1], pair[0]]);
                const polygonCoordinates = sortPointsForPolygon(flippedCoords);
                const polygonFeature = new ol.Feature({
                    geometry: new ol.geom.Polygon([polygonCoordinates])
                });
                polygonFeature.setStyle(new ol.style.Style({
                    fill: new ol.style.Fill({ color: color}),
                    stroke: new ol.style.Stroke({ color: 'black', width: 0 })
                }));
                return polygonFeature;
            }

            // Add features to the vector layer
            let colors = ['red', 'blue', 'purple']; // Array of colors to cycle through
            let colorIndex = 0; // Start with the first color
            // 2. Get the map's layers collection
            const layersCollection = map.getLayers();
            var structured_data = {
                [asn2_name]: data['asn2_pops'],
                [asn1_name]: data['asn1_pops'],
                "Overlap": data['overlapping_pops']
            };
            // 3. Create a new vector layer
            // get the legend container
            const legendContainer = document.getElementById('legend');
            for (const [ispName, locations] of Object.entries(structured_data)) {
                const current_isp_color = colors[colorIndex]; // Get the color for this iteration

                const currentISPDotsLayer = new ol.layer.Vector({
                    source: new ol.source.Vector(),
                    opacity: 1
                });
                for (const location of locations) {
                    if (location.hasOwnProperty('both_pops_here') &&location['both_pops_here'] === true) {
                        continue;
                    }
                    var location_coords = location['location'];

                    currentISPDotsLayer.getSource().addFeature(createFacilityDot(location['org_name'], location_coords, current_isp_color, location['city'], location['country'], location['state'], location['isp_type_in_peering_db'], location['port_capacity']));
                }
                if (ispName !== "Overlap") {
                    const all_location_coords = locations.map(location => location['location']);
                    console.log(ispName, all_location_coords);

                    const polygonFeature = createPolygonFeature(all_location_coords, colors[colorIndex]);

                    const currentPolygonLayer = new ol.layer.Vector({
                        source: new ol.source.Vector(),
                        opacity: 0.5  // 50% opacity
                    });
                    currentPolygonLayer.getSource().addFeature(polygonFeature);
                    layersCollection.push(currentPolygonLayer);
                }

                //Add dots layer after so its on top
                layersCollection.push(currentISPDotsLayer);

                // Create legend entry for ISP dots
                const ispLegendEntry = document.createElement('div');
                ispLegendEntry.innerHTML = `<span class="color_block" style="background-color: ${current_isp_color}"></span>${ispName}`;
                legendContainer.appendChild(ispLegendEntry);

                colorIndex = (colorIndex + 1) % colors.length; // Cycle to the next color
            }

            // Click event handler for popups
            const popupOverlay = new ol.Overlay({
                element: document.createElement('div'),
                offset: [5, 5],
                positioning: 'center-left'
            });
            map.addOverlay(popupOverlay);

            const popupContainer = popupOverlay.getElement();
            popupContainer.className = 'popup-content';

            map.on('click', function(evt) {
                const feature = map.forEachFeatureAtPixel(evt.pixel, function(feature) {
                    return feature;
                });
                if (feature) {
                    const coordinates = feature.getGeometry().getCoordinates();
                    const ispName = feature.get('name');
                    const city = feature.get('city');
                    const country_code = feature.get('country_code');
                    const state = feature.get('state');
                    const isp_type = feature.get('isp_type');
                    const port_capacity = feature.get('port_capacity');
                    popupContainer.innerHTML = `<b>${ispName}</b><br/>
                                                City: ${city}<br/>
                                                Country: ${country_code}<br/>
                                                State: ${state}<br/>
                                                ISP Type: ${isp_type.toUpperCase()}<br/>
                                                Port Capacity: ${port_capacity.toLocaleString()}<br/>
                                                Both ISP at this POP: ${feature.get('both_pops_here') ? 'Yes' : 'No'}`;
                    popupOverlay.setPosition(evt.coordinate);
                } else {
                    popupOverlay.setPosition(undefined);
                    popupContainer.innerHTML = '';
                }
            });
        })
        .catch(error => {
            // Handle any errors here
            console.error(error);
            // Display error message
            const errorContainer = document.createElement('div');
            errorContainer.innerHTML = "Error: Unable to load map data. Please try again later."
            container.appendChild(errorContainer);
        });
