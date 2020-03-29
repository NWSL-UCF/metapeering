function [element] = readfileelement(file,latitude,longtitude)
%% read the grid element corresponding to the latitude and longitude
%Example call: <variable> = readfileelement('ciesin/glareag.asc',40.70,-73.92)

ncols = 8640;
nrows = 3432;
cellsize = 2.5/60.0;
xllcorner = -180.0;
yllcorner = -58.0;

%% sanity checks
if (longtitude > 180.0 || longtitude < -180.0 )
    longtitude
    return;
end;
if (latitude > 85.0 || latitude < -58.0 )
    latitude
    element = -1;
    return;
end;

x = ceil( (longtitude-xllcorner)/cellsize ) + 1;
if (x > ncols)
    x = ncols;
end;

y = nrows - ceil( (latitude-yllcorner)/cellsize ); 
if (y == 0)
    y = 0;
end;

fid = fopen(file);
C = textscan(fid, '%f', x, 'headerLines', y-1);
fclose(fid);

C = cell2mat(C);
element = C(x);

%dlmwrite('x.txt', x, '-append');
%dlmwrite('y.txt', y, '-append');

return;


