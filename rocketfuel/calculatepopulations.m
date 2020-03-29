function [populations] = calculatepopulations()
%% read the grid element corresponding to the latitude and longitude

% read the cities and their grid positions
[cities, latitudes, longitudes] = textread('cities.txt', '%s %f %f', 'delimiter', '\t' );

%gridpopulation = zeros(8640,3432);
%fid = fopen('ciesin/glp05ag.asc');
%for i = 1:1
%    for j = 1:1
%        gridpopulation(j,i) = textscan(fid, '%f');        
%    end;
%end;
%fclose(fid);
%gridpopulation
%size(gridpopulation)
%return;

% calculate the population in roughly 50x50 km^2 area around of each city
%% HERE: need to correct this w/ possibly a better method
cellsize = 2.5/60.0;

populations = 0;
[t1,t2] = size(cities);
for i=1:t1
    leftarea = 2500.0; %% km^2
    lat = latitudes(i);
    lon = longitudes(i);
    current_pop = readfileelement('ciesin/glp05ag.asc',lat,lon);
    leftarea = leftarea - readfileelement('ciesin/glareag.asc',lat,lon);
    sw_lat = lat;
    nw_lat = lat;
    se_lat = lat;
    ne_lat = lat;
    sw_lon = lon;
    nw_lon = lon;
    se_lon = lon;
    ne_lon = lon;
    while (leftarea > 0.0)
        sw_lat = sw_lat - cellsize;
        sw_lon = sw_lon - cellsize;
        nw_lat = nw_lat + cellsize;
        nw_lon = nw_lon - cellsize;
        se_lat = se_lat - cellsize;
        se_lon = se_lon + cellsize;
        ne_lat = ne_lat + cellsize;
        ne_lon = ne_lon + cellsize;

        beginning_leftarea = leftarea;
        
        currentpoint = sw_lat;
        while (leftarea > 0.0  &&  currentpoint < nw_lat)
            current_pop = current_pop + readfileelement('ciesin/glp05ag.asc',currentpoint,sw_lon);
            leftarea = leftarea - readfileelement('ciesin/glareag.asc',currentpoint,sw_lon);
            currentpoint = currentpoint + cellsize;
        end;

        currentpoint = nw_lon;
        while (leftarea > 0.0  &&  currentpoint < ne_lon)
            current_pop = current_pop + readfileelement('ciesin/glp05ag.asc', nw_lat, currentpoint);
            leftarea = leftarea - readfileelement('ciesin/glareag.asc', nw_lat, currentpoint);
            currentpoint = currentpoint + cellsize;
        end;

        currentpoint = ne_lat;
        while (leftarea > 0.0  &&  currentpoint > se_lat)
            current_pop = current_pop + readfileelement('ciesin/glp05ag.asc',currentpoint,ne_lon);
            leftarea = leftarea - readfileelement('ciesin/glareag.asc',currentpoint,ne_lon);
            currentpoint = currentpoint - cellsize;
        end;

        currentpoint = se_lon;
        while (leftarea > 0.0  &&  currentpoint > sw_lon)
            current_pop = current_pop + readfileelement('ciesin/glp05ag.asc', se_lat, currentpoint);
            leftarea = leftarea - readfileelement('ciesin/glareag.asc', se_lat, currentpoint);
            currentpoint = currentpoint - cellsize;
        end;

        leftarea
        % if it is an island and the whole island is covered, then stop
        if (beginning_leftarea == leftarea)
            leftarea = 0.0;
        end;
    end;
    
    populations(i) = current_pop;
    populations
    current_pop
    current_pop = 0;
end;

%dlmwrite('populations.txt', populations, 'delimiter', '\t');
dlmwrite('populations.txt', populations, '-append', 'delimiter', '\n');

return;
