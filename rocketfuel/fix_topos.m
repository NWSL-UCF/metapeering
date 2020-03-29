%% which topology to use
TOPOLOGY = 5;

if (TOPOLOGY == 1) %% TELSTRA
    %% nodes 108, links 306, Telstra (Australia), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('1221/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1221/weights.intra', '%s %s %f');
    fidlat = fopen('1221/latencies.intra', 'a');
    fidwei = fopen('1221/weights.intra', 'a');
elseif (TOPOLOGY == 2) %% SPRINTLINK
    %% nodes 315, links 1944, Sprintlink (US), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('1239/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1239/weights.intra', '%s %s %f');
    fidlat = fopen('1239/latencies.intra', 'a');
    fidwei = fopen('1239/weights.intra', 'a');
elseif (TOPOLOGY == 3) %% EBONE
    %% nodes 87, links 322, Ebone (Europe), BIDIRECTIONAL, CONNECTED
    %% nodes 87, links 407, Ebone (Europe), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('1755/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1755/weights.intra', '%s %s %f');
    E2E_t_avg_range = 10:1:150; %% 57+ is satisfactory
    fidlat = fopen('1755/latencies.intra', 'a');
    fidwei = fopen('1755/weights.intra', 'a');
elseif (TOPOLOGY == 4) %% TISCALI
    %% nodes 161, links 656, Tiscali (Europe), BIDIRECTIONAL, CONNECTED
    %% nodes 161, links 900, Tiscali (Europe), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('3257/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('3257/weights.intra', '%s %s %f');
    fidlat = fopen('3257/latencies.intra', 'a');
    fidwei = fopen('3257/weights.intra', 'a');
elseif (TOPOLOGY == 5) %% EXODUS
    %% nodes 79, links 294, Exodus (US), BIDIRECTIONAL, CONNECTED
    %% nodes 79, links 353, Exodus (US), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('3967/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('3967/weights.intra', '%s %s %f');
    E2E_t_avg_range = 10:1:150; %% 106+ is satisfactory
    fidlat = fopen('3967/latencies.intra', 'a');
    fidwei = fopen('3967/weights.intra', 'a');
elseif (TOPOLOGY == 6) %% ABOVENET
    %% nodes 141, links 748, Abovenet (US), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('6461/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('6461/weights.intra', '%s %s %f');
    fidlat = fopen('6461/latencies.intra', 'a');
    fidwei = fopen('6461/weights.intra', 'a');
end;
%% end-to-end delay requirement for premium class traffic (milliseconds)
%E2E_t_avg_range = 106:1:150;

[numoflinks,n] = size(A);

%% CHECK IF THE LATENCY AND WEIGHTS DATA MATCH
match = 1;
for i=1:numoflinks
    if (~strcmp(A(i),C(i)) || ~strcmp(A(i),C(i)))
        match = 0;
    end;
end;
match

%% CONSTRUCT THE LIST OF ROUTERS IN THE TOPOLOGY
routers(1) = A(1);
for i=2:numoflinks
    %% CHECK FOR MULTIPLE ENTRIES
    if (findfirstarrayelement(routers,A(i)) == 0)
        [routers_size,n] = size(routers);
        routers(routers_size+1,1) = A(i);
    end;
end;
for i=1:numoflinks
    %% CHECK FOR MULTIPLE ENTRIES
    if (findfirstarrayelement(routers,B(i)) == 0)
        [routers_size,n] = size(routers);
        routers(routers_size+1,1) = B(i);
    end;
end;
routers = sort(routers);
routers

%% CONSTRUCT THE ADJACENCY, THE WEIGHT, AND THE LATENCY MATRICES
multiple_links = 0;
[numofnodes,n] = size(routers);
Adj = zeros(numofnodes,numofnodes);
Lat = zeros(numofnodes,numofnodes);
Wei = zeros(numofnodes,numofnodes);
for i=1:numoflinks
    x = findfirstarrayelement(routers,A(i));
    y = findfirstarrayelement(routers,B(i));
    %% CHECK FOR MULTIPLE LINKS
    if (Adj(x,y) == 1)
        multiple_links = multiple_links + 1;
        Adj(x,y)
        multiple_links
    end;
    Adj(x,y) = 1;
    Lat(x,y) = latency(i); 
    Wei(x,y) = weight(i); 
end;

%Adj
numofnodes
numoflinks

% find minimum latency and minimum weight
[minlatency,tempind] = min(latency);
[minweight,tempind] = min(weight);

%% SANITY CHECK FOR CONNECTIVITY
[connected, TC] = TestConnectivity(Adj);
connected
%%[Connectivity, NumofComponents, GlobalRoot, GlobalParent, GlobalCycle]=Dfs(Adj)
% if (connected) 
%     fclose(fidlat);
%     fclose(fidwei);
%     return;
% end;
 
% get the positions of all available cities
[cities, latitudes, longitudes] = textread('cities.txt', '%s %f %f', 'delimiter', '\t' );
[numofcities,k] = size(cities);

routercities = strrep(strtok(routers, ','), '+', ' ');
routercities = strrep(routercities, '0', '');
routercities = strrep(routercities, '1', '');
routercities = strrep(routercities, '2', '');
routercities = strrep(routercities, '3', '');
routercities = strrep(routercities, '4', '');
routercities = strrep(routercities, '5', '');
routercities = strrep(routercities, '6', '');
routercities = strrep(routercities, '7', '');
routercities = strrep(routercities, '8', '');
routercities = strrep(routercities, '9', '');

% check if all the router cities exist in the list of cities
for i=1:numofnodes
    if (findfirstarrayelement(cities,routercities(i)) == 0)
        routers(i)
        return;
    end;
end;

linksadded = 0;
for i=1:numofcities
    ithcityrouters = routers(find(strcmp(routercities, cities(i))));
    [numofithcityrouters,tempind] = size(ithcityrouters);
    ithcityrouters

    if (numofithcityrouters > 0)
        %% the following does a circular topology
        x = findfirstarrayelement(routers,ithcityrouters(1));
        y = findfirstarrayelement(routers,ithcityrouters(numofithcityrouters));
        if (Adj(x,y) == 0)
            Adj(x,y) = 1;
            linksadded = linksadded + 1;
            % add a link from x to y
            fprintf(fidlat, '%s %s %d\n', char(ithcityrouters(1)), char(ithcityrouters(numofithcityrouters)), minlatency);
            fprintf(fidwei, '%s %s %.1f\n', char(ithcityrouters(1)), char(ithcityrouters(numofithcityrouters)), minweight);
        end;
        if (Adj(y,x) == 0)
            Adj(y,x) = 1;
            linksadded = linksadded + 1;
            % add a link from y to x
            fprintf(fidlat, '%s %s %d\n', char(ithcityrouters(numofithcityrouters)), char(ithcityrouters(1)), minlatency);
            fprintf(fidwei, '%s %s %.1f\n', char(ithcityrouters(numofithcityrouters)), char(ithcityrouters(1)), minweight);
        end;
        firstind = 1;
        for j=2:numofithcityrouters
            x = findfirstarrayelement(routers,ithcityrouters(j-1));
            y = findfirstarrayelement(routers,ithcityrouters(j));
            if (Adj(x,y) == 0)
                Adj(x,y) = 1;
                linksadded = linksadded + 1;
                % add a link from x to y
                fprintf(fidlat, '%s %s %d\n', char(ithcityrouters(j-1)), char(ithcityrouters(j)), minlatency);
                fprintf(fidwei, '%s %s %.1f\n', char(ithcityrouters(j-1)), char(ithcityrouters(j)), minweight);
            end;
            if (Adj(y,x) == 0)
                Adj(y,x) = 1;
                linksadded = linksadded + 1;
                % add a link from y to x
                fprintf(fidlat, '%s %s %d\n', char(ithcityrouters(j)), char(ithcityrouters(j-1)), minlatency);
                fprintf(fidwei, '%s %s %.1f\n', char(ithcityrouters(j)), char(ithcityrouters(j-1)), minweight);
            end;
        end;
    end;
    
    %% the following does a full mesh topology
%    for j=1:numofithcityrouters
%        for k=1:numofithcityrouters
%            if (j ~= k)
%                x = findfirstarrayelement(routers,ithcityrouters(j));
%                y = findfirstarrayelement(routers,ithcityrouters(k));
%                if (Adj(x,y) == 0)
%                    Adj(x,y) = 1;
%                    linksadded = linksadded + 1;
%                    % add a link from x to y
%                    fprintf(fidlat, '%s %s %d\n', char(ithcityrouters(j)), char(ithcityrouters(k)), minlatency);
%                    fprintf(fidwei, '%s %s %.1f\n', char(ithcityrouters(j)), char(ithcityrouters(k)), minweight);
%                end;
%                if (Adj(y,x) == 0)
%                    Adj(y,x) = 1;
%                    linksadded = linksadded + 1;
%                    % add a link from y to x
%                    fprintf(fidlat, '%s %s %d\n', char(ithcityrouters(k)), char(ithcityrouters(j)), minlatency);
%                    fprintf(fidwei, '%s %s %.1f\n', char(ithcityrouters(k)), char(ithcityrouters(j)), minweight);
%                end;
%            end;
%        end;
%    end;
end;
linksadded


%% SANITY CHECK FOR CONNECTIVITY
[connected, TC] = TestConnectivity(Adj);
connected

fclose(fidlat);
fclose(fidwei);

