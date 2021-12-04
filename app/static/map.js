function listToCoordinates(isp_a)
{
  var listOfLocationsA = [];
  var medLong = [];
  var medLat = [];

  for (var i = 0; i < isp_a.length; i++)
  {
    var temp = {'x': isp_a[i].location[1], 'y': isp_a[i].location[0]};

    medLong.push(isp_a[i].location[1]);
    medLat.push(isp_a[i].location[0]);

    listOfLocationsA.push(temp);
  }

  var centerA = median(medLong);
  var centerB = median(medLat);

  var res = [];

  res = sortByAngle(centerA, centerB, listOfLocationsA);

  res.push(res[0]);
  var tempArr = [];
  tempArr.push(res);

  return tempArr;
}

function median(values){
  if (values.length === 0) throw new Error("No inputs");

  values.sort(function(a,b){
    return a-b;
  });

  var half = Math.floor(values.length / 2);

  if (values.length % 2)
    return values[half];

  return (values[half - 1] + values[half]) / 2.0;
}

// Sort coordinates by the median values
function sortByAngle(centerX, centerY, isp){
  var sorted = [];

  for (var i = 0; i < isp.length; i++)
  {
    var m = 0;

    var temp = isp[i];

    if (centerX - temp.x != 0)
      m = (centerY - temp.y)/(centerX - temp.x);

    var angleTemp = 0;

    if (m == 0)
    {
      if (temp.y > centerY)
        angleTemp = 180;
    }

    else if (temp.x >= centerX)
    {
      angleTemp = 90 - (Math.atan(m) * (180 / Math.PI));
    }

    else if (temp.x < centerX)
    {
      angleTemp = 270 - (Math.atan(m) * (180/Math.PI));
    }

    sorted.push({'x':temp.x, 'y':temp.y, 'angle':angleTemp});
  }

  var pointsSorted = sorted.sort((a, b) => a.angle - b.angle);
  var res = [];

  for (var i = 0; i < pointsSorted.length; i++)
  {
    var temp = [];
    temp.push(pointsSorted[i].x);
    temp.push(pointsSorted[i].y);
    res.push(temp);
  }

  return res;
}

function getData(points)
{
  var data = {
    "type": "FeatureCollection",
    "features": [
    {
      "type" : "Feature",
      "geometry": {
        "type" : "Polygon",
        "coordinates": points
      }
    }
    ]
  };

  return data;
}

function pointData(list)
{
  let feat = [];
  for (var i = 0; i < list.length; i++)
  {
    var points = [];
    points.push(list[i].location[1]);
    points.push(list[i].location[0]);

    feat.push(
    {
      "type" : "Feature",
      "properties":
      {
        "name": list[i].org_name,
        "city": list[i].city,
        "state": list[i].state
      },

      "geometry":
      {
        "type" : "Point",
        "coordinates": points
      }
    });
  }

  return feat;
}

var l1 = listToCoordinates(isp_a);
var l2 = listToCoordinates(isp_b);
var data = getData(l1);
var data2 = getData(l2);
var pt = pointData(isp_a);
var ptB = pointData(isp_b);

var points =  {
  "type": "FeatureCollection",
  "features": pt
};

var pointsB =  {
  "type": "FeatureCollection",
  "features": ptB
};

const width = 900;
const height = 600;
const svg = d3.select("#map").append("svg")
    .attr("width", width)
    .attr("height", height);

const projection = d3.geoAlbersUsa()
    .translate([width / 2, height / 2]) // translate to center of screen
    .scale([1000]); // scale things down so see entire US

const path = d3.geoPath().projection(projection);

d3.json("https://gist.githubusercontent.com/Bradleykingz/3aa5206b6819a3c38b5d73cb814ed470/raw/a476b9098ba0244718b496697c5b350460d32f99/us-states.json", function(error, uState) {
if (error) throw error;
  var div = d3.select("#map").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);
  svg.selectAll('path')
        .data(uState.features)
        .enter()
        .append("path")
        .attr("d", path);
  svg.selectAll('.polyA')
        .data(data.features)
        .enter()
        .append('path')
        .attr("d", path)
        .attr('class', 'polyA');
  svg.selectAll('.polyB')
        .data(data2.features)
        .enter()
        .append('path')
        .attr("d", path)
        .attr('class', 'polyB');
  svg.selectAll('.circle')
        .data(points.features)
        .enter()
        .append('path')
        .attr("d", path)
        .attr('class', 'circle')
        .on("mouseover", function(d) {
          div.transition()
            .duration(200)
            .style("opacity", .9);
          div.html(d.properties.name + "</br>" + d.properties.city + ", " + d.properties.state)
            .style("left", (d3.event.pageX + 10) + "px")
            .style("top", (d3.event.pageY - 28) + "px")
          })
        .on('mouseout', function (d) {
          div.transition()
            .duration('50')
            .attr('opacity', '1');
              //Makes the new div disappear:
          div.transition()
            .duration('50')
            .style("opacity", 0);
         });
  svg.selectAll('.circleB')
        .data(pointsB.features)
        .enter()
        .append('path')
        .attr("d", path)
        .attr('class', 'circleB')
        .on("mouseover", function(d) {
          div.transition()
            .duration(200)
            .style("opacity", .9);
          div.html(d.properties.name + "</br>" + d.properties.city + ", " + d.properties.state)
            .style("left", (d3.event.pageX + 10) + "px")
            .style("top", (d3.event.pageY - 28) + "px")
        })
        .on('mouseout', function (d) {
          div.transition()
            .duration('50')
            .attr('opacity', '1');
           //Makes the new div disappear:
          div.transition()
            .duration('50')
            .style("opacity", 0);
         });

  svg.append('legend')
        .attr('class', 'legend')
        .attr('width', 50)
        .attr('height', 50)
        .append("circle").attr("cx",200).attr("cy",130).attr("r", 6).style("fill", "#69b3a2")
        .append("circle").attr("cx",200).attr("cy",130).attr("r", 6).style("fill", "#69b3a2")
        .append("circle").attr("cx",200).attr("cy",130).attr("r", 6).style("fill", "#69b3a2")
        .append("text").attr("x", 220).attr("y", 130).text("variable A").style("font-size", "15px").attr("alignment-baseline","middle")
        .append("text").attr("x", 220).attr("y", 130).text("variable A").style("font-size", "15px").attr("alignment-baseline","middle")
        .append("text").attr("x", 220).attr("y", 130).text("variable A").style("font-size", "15px").attr("alignment-baseline","middle")
  });
