%% which topology to use
TOPOLOGY = 2;
%% maximum allowed link utilization
MAX_LINK_UTIL = 0.95; %% with +/- 1% error due to precision issues
%% half of the buffer size in packets
K = 60; 
%% edge-to-edge loss probability requirement for premium class traffic (%)
%E2E_p_avg_range = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.5];
E2E_p_avg_range = [0.001, 0.01, 0.1, 0.5, 1, 5, 10, 20, 30, 40, 50];

if (TOPOLOGY == 1) %% TELSTRA
    %% nodes 108, links 414, Telstra (Australia), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('1221/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1221/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 5;
    DISTANCETHRESH = 4;
    ispname = 'telstra';
elseif (TOPOLOGY == 2) %% SPRINTLINK
    %% nodes 315, links 2339, Sprintlink (US), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('1239/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1239/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 9;
    DISTANCETHRESH = 5;
    ispname = 'sprintlink';
elseif (TOPOLOGY == 3) %% EBONE
    %% nodes 87, links 407, Ebone (Europe), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('1755/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1755/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 6;
    DISTANCETHRESH = 4;
    ispname = 'ebone';
elseif (TOPOLOGY == 4) %% TISCALI
    %% nodes 161, links 900, Tiscali (Europe), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('3257/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('3257/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 8;
    DISTANCETHRESH = 4;
    ispname = 'tiscali';
elseif (TOPOLOGY == 5) %% EXODUS
    %% nodes 79, links 353, Exodus (US), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('3967/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('3967/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 6;
    DISTANCETHRESH = 4;
    ispname = 'exodus';
elseif (TOPOLOGY == 6) %% ABOVENET
    %% nodes 141, links 925, Abovenet (US), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('6461/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('6461/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 9;
    DISTANCETHRESH = 3;
    ispname = 'abovenet';
end;

%% utilization levels to be calculated
urange = 0.99:-0.1:0.09;

%% traffic model to be used: 1 -- Poisson, 2 -- MMPP
TRAFFIC_MODEL = 2;
if (TRAFFIC_MODEL == 2) % if MMPP, then set the MMPP parameters
    a_mmpp = 0.5;
    r_mmpp = 4;
end;
if (TRAFFIC_MODEL == 3) % if LRD, then set the Hurst parameter
    Hurst = 0.75;
end;

%% handling infeasible links: 1 -- JEC
INFEASIBLE_LINKS = 1;

%% packet size
pkt_size = 1024 %% bytes

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

%% SANITY CHECK FOR BIDIRECTIONALITY -- 
%% ISP backbone links must be bidirectional
bidirectional = 1;
for i=1:numoflinks
    if (Adj(x,y) == 1)
        if (Adj(y,x) == 0)
            bidirectional = 0;
        end;
    end;
end;
bidirectional
if (bidirectional == 0)
    return;
end;

%% SANITY CHECK FOR CONNECTIVITY
% [connected, TC] = TestConnectivity(Adj);
% connected
% %%[Connectivity, NumofComponents, GlobalRoot, GlobalParent, GlobalCycle]=Dfs(Adj)
% %% FIX IF THERE ARE DISJOINT SUBSETS
% if (~connected) %% HERE: currently we are just exiting instead of fixing
%     return;
% end;
 
%% CONSTRUCT THE COST MATRIX
Cost = zeros(numofnodes,numofnodes);
Cost = Wei;
for i=1:numofnodes
    for j=1:numofnodes
        if (Cost(i,j) == 0  &&  i ~= j)
            Cost(i,j) = Inf;
        end;
    end;
end;
%Cost

%% CALCULATE THE ALL PAIRS SHORTEST PATH
%% Floyd-Warshall algorithm
[SP, Prev] = AllPairsShortestPath(Cost);

%% CONSTRUCT THE ROUTING MATRIX
numofflows = numofnodes*numofnodes;
%R = zeros(numofflows,numoflinks,'int8');
R = zeros(numofflows,numoflinks,'single');
% for all flows..
for i=1:numofnodes
    for j=1:numofnodes
        if (i ~= j)
            flowid = (i-1)*numofnodes + j;
            introuter = Prev(i,j);
            last = j;
            % mark all the links this flow is passing through
            count = 0;
            while (introuter ~= i)
                linkid = findlink(routers(introuter),routers(last),A,B);
                if (linkid == 0)
                    linkid
                    introuter
                    routers(introuter)
                    last
                    routers(last)
                end;
                R(flowid,linkid) = 1;
                last = introuter;
                introuter = Prev(i,introuter);
                
                count = count + 1;
                if (count > numofnodes) % there is a loop in routing
                    count
                    return;
                end;
            end;
            % don't forget the very first link this flow traverses
            linkid = findlink(routers(introuter),routers(last),A,B);    
            R(flowid,linkid) = 1;
        end;
    end;
end;

%% FIND LINKS UNUSED DUE TO ROUTING
numofunusedlinks = 0;
for i=1:numoflinks
    if (sum(R(:,i)) == 0)
        numofunusedlinks = numofunusedlinks + 1;
        unusedlinks(numofunusedlinks) = i;
    end;
end;
numofunusedlinks

%% CONSTRUCT THE CAPACITY MATRIX
%% Select the highest degree node and make a BFS. 
%% Assign lower capacity to the links as getting deeper in the BFS tree.
%% find the max degree node
Degrees = zeros(numofnodes,1);
for i=1:numofnodes
    for j=1:numoflinks
        if (strcmp(routers(i),A(j)))
            Degrees(i) = Degrees(i) + 1;
        end;
    end;
end;
%Degrees

%% make BFS starting from the maxdegree node
[maxdegree,maxindices] = max(Degrees);
[Distance,Parent,Layers,NumofLayers]= Bfs(Adj,maxindices(1));
%Distance
%Parent

%% assign capacities to the links (in Mb/s)
capacitylevels = [40000, 10000, 2500, 620, 155, 45, 10];
[tempind, numofcapacitylevels] = size(capacitylevels);
Capacities = zeros(numoflinks,1);
for i=1:numoflinks
    xid = findfirstarrayelement(routers,A(i));
    yid = findfirstarrayelement(routers,B(i));
    maxdistance = max(Distance(xid),Distance(yid));
    % assure that no link has less than 10Mb/s capacity
    Capacities(i) = capacitylevels( min(numofcapacitylevels, maxdistance) );
end;
%Capacities

%% FORM THE TRAFFIC VECTOR FROM THE TRAFFIC MATRIX
%% the set of edge nodes: 1 in the array element indicates edge node
edgenodes = zeros(numofnodes,1);
%% first include all nodes having either degree < 3 or distance > 4
for i=1:numofnodes
    if (Degrees(i) < DEGREETHRESH  ||  Distance(i) > DISTANCETHRESH)
        edgenodes(i) = 1;
    end;
end;

% assure that there exists at least one edge router at each city
%edgecities = strrep(strtok(routers(find(edgenodes)), ','), '+', ' ');
topocities = strrep(strtok(routers, ','), '+', ' ');
topocities = strrep(topocities, '0', '');
topocities = strrep(topocities, '1', '');
topocities = strrep(topocities, '2', '');
topocities = strrep(topocities, '3', '');
topocities = strrep(topocities, '4', '');
topocities = strrep(topocities, '5', '');
topocities = strrep(topocities, '6', '');
topocities = strrep(topocities, '7', '');
topocities = strrep(topocities, '8', '');
topocities = strrep(topocities, '9', '');

for i=1:numofnodes
    currentcity = topocities(i);
    if ( sum(edgenodes .* strcmp(topocities, currentcity)) < 1 )
        % need to add a new router to the set of edge nodes
        currentcity
        routerindicesforcurrentcity = find(strcmp(topocities, currentcity));
        % select the max degree router in the city
        [t1, t2] = max(Degrees(routerindicesforcurrentcity));
        maxdegreerouterforcurrentcity = routers(routerindicesforcurrentcity(t2));        
    end;
end;

%return;

% need to identify the links unused by the current assumption
BeforeTVector = zeros(numofflows,1);
for i=1:numofnodes
    for j=1:numofnodes
        if (i ~= j  &&  edgenodes(i)  &&  edgenodes(j))
            flowid = (i-1)*numofnodes + j;
            %% just assign a traffic of 1 temporarily
            BeforeTVector(flowid) = 1.0;
        end;
    end;
end;
BeforeQ = R' * BeforeTVector;

%% increase the set of edge nodes by including the nodes next to the links 
%% unused by the current set of edge nodes
% currunusedlinks = find(BeforeQ <= 0);
% [t1,t2] = size(currunusedlinks);
% for i=1:t1
%     edgenodes(findfirstarrayelement(routers,A(currunusedlinks(i)))) = 1;
%     edgenodes(findfirstarrayelement(routers,B(currunusedlinks(i)))) = 1;
% end;
% return;

%% HERE: just tried assigning all nodes as edge
%% edgenodes = ones(numofnodes,1);

%%%% Gravity model 

% get the positions of all available cities
[cities, latitudes, longitudes] = textread('cities.txt', '%s %f %f', 'delimiter', '\t' );

% prepare the set of edge cities for the topology under consideration
edgecities = strrep(strtok(routers(find(edgenodes)), ','), '+', ' ');
edgecities = strrep(edgecities, '0', '');
edgecities = strrep(edgecities, '1', '');
edgecities = strrep(edgecities, '2', '');
edgecities = strrep(edgecities, '3', '');
edgecities = strrep(edgecities, '4', '');
edgecities = strrep(edgecities, '5', '');
edgecities = strrep(edgecities, '6', '');
edgecities = strrep(edgecities, '7', '');
edgecities = strrep(edgecities, '8', '');
edgecities = strrep(edgecities, '9', '');

% calculate frequency of each edge city
edgecityfrequencies = 0;
for i=1:sum(edgenodes)
    [t1,t2] = size(find(strcmp(edgecities, edgecities(i))));
    edgecityfrequencies(i) = t1;
end;

% get the populations of all available cities
[populations] = textread('populations.txt', '%f', 'delimiter', '\n' );

% calculate the population of each edge city (divide by the frequency)
edgecitypopulations = 0;
for i=1:sum(edgenodes)
    cityindex = findfirstarrayelement(cities, edgecities(i));
    edgecitypopulations(i) = populations(cityindex);
    edgecitypopulations(i) = edgecitypopulations(i) / edgecityfrequencies(i);

    % sanity check
    if (edgecitypopulations(i) <= 0)
        edgecitypopulations(i)
        return;
    end;
end;
edgecitypopulations

% normalize the edge city populations to their minimum
minpopulation = min(edgecitypopulations);
edgecitymasses = edgecitypopulations ./ minpopulation;

% calculate the gravity product factor for all g2g flows
GravityProducts = zeros(numofflows,1);
for i=1:numofnodes
    for j=1:numofnodes
        flowid = (i-1)*numofnodes + j;
        if (i ~= j  &&  edgenodes(i)  &&  edgenodes(j))
            edgenodei = sum(edgenodes(1:i));
            edgenodej = sum(edgenodes(1:j));
            GravityProducts(flowid) = edgecitymasses(edgenodei) * edgecitymasses(edgenodej);
        else
            GravityProducts(flowid) = Inf;
        end;
    end;
end;
[t1,t2] = size(find(GravityProducts < 1.0));
if (t1 > 0) % sanity check: are there any products less than 1.0?
    t1
    return;
end;

% find the flow with the minimum product factor among all g2g flows
[minprodflow, minprodflowind] = min(GravityProducts);

% find the min-product-factor flow's maximum possible rate
minflowrate = MAX_LINK_UTIL*min(Capacities(find(R(minprodflowind,:))));

% calculate rates for all g2g flows based on the min-product-factor flow
TVector = zeros(numofflows,1);
for i=1:numofnodes
    for j=1:numofnodes
        %% Need to identify edge routers
        %% assumption: edge routers have either degree < 3 or distance > 4
        %% old assumption: each edge-to-edge flow is 0.23Mb/s for Exodus
        %% old assumption: each edge-to-edge flow is 0.0095Mb/s for Ebone
        if (i ~= j  &&  edgenodes(i)  &&  edgenodes(j))
            flowid = (i-1)*numofnodes + j;
            % assign min capacity of all links the flow is
            % traversing
            % TVector(flowid) = 0.23;
            % Need to multiply by MAX_LINK_UTIL so that 100% utilization is
            % avoided.
            TVector(flowid) = GravityProducts(flowid)*minflowrate;
        end;
    end;
end;

BeforeTVector = TVector;
BeforeQ = R' * BeforeTVector;

feasible = 0;
while (feasible == 0)
    %% nonzero traffic flows
    numofnonzeroflows = size(find(TVector));
    nonzeroflowspercentage = 100*numofnonzeroflows(1) / numofflows;
    nonzeroflowspercentage
    
    %% CALCULATE LOAD ON INDIVIDUAL LINKS
    Q = 0;
    Q = R' * TVector;
    %Q = TVector' * R;
    %Q

    %% CHECK FEASIBILITY
    feasible = 1;
    unfeasiblelinkscount = 0;
    overloads = 0;
    unfeasiblelinks = 0;
    for i=1:numoflinks
        %        if (Q(i) >= Capacities(i))
        %% if (Q(i) ./ Capacities(i) - MAX_LINK_UTIL > 0) %% limit the link utilization
        if (Q(i) ./ Capacities(i) - MAX_LINK_UTIL > 0.01) %% +/- 1% error due to Matlab's precision issues
            feasible = 0;
            %Q(i)
            %Capacities(i)
            
            unfeasiblelinkscount = unfeasiblelinkscount + 1;
            unfeasiblelinks(unfeasiblelinkscount) = i;
            overloads(unfeasiblelinkscount) = Q(i) - Capacities(i);
        end;
    end;
    
    % if not feasible, try to fix it
    if (feasible == 0)
        % find the most overloaded link
        [t1,t2] = max(overloads);
        mostoverloaded = unfeasiblelinks(t2);
        
        if (INFEASIBLE_LINKS == 1)
            % increase the capacity of the link so that the load corresponds to
            % MAX_LINK_UTIL of the link capacity.
            mostoverloaded
            Q(mostoverloaded)
            Capacities(mostoverloaded) = Q(mostoverloaded) ./ MAX_LINK_UTIL;
            Capacities(mostoverloaded)
        elseif (INFEASIBLE_LINKS == 2)
            % if upgrade to the link is possible, then do the minimum necessary upgrade first
            if (capacitylevels(1) > Capacities(mostoverloaded))
                bettercapacitylevels = capacitylevels(find(capacitylevels > Capacities(mostoverloaded)));
                Capacities(mostoverloaded) = min(bettercapacitylevels);
            else
                % calculate the multiplication factor
                factor = Capacities(mostoverloaded) / Q(mostoverloaded)
                %        if (Capacities(mostoverloaded) / Q(mostoverloaded) > MAX_LINK_UTIL)
                if (factor > MAX_LINK_UTIL)
                    factor = MAX_LINK_UTIL
                end;
                % find flows traversing this link
                traversingflows = 0;
                traversingflows = find(R(:,mostoverloaded));
                TVector(traversingflows) = factor * TVector(traversingflows);
            end;
%         elseif (INFEASIBLE_LINKS == 3) % HERE HERE
%             % find the largest load per link
%             [t1,largestloaded] = max(Q);
%             largestload = Q(largestloaded);
%             largestloaded
%             largestload
%             
%             INFEASIBLE_LINKS = 1;
%             
%             % if upgrade to the link is possible, then do the minimum necessary upgrade first
%             if (capacitylevels(1) > Capacities(largestloaded))
%                 bettercapacitylevels = capacitylevels(find(capacitylevels > Capacities(largestloaded)));
%                 Capacities(largestloaded) = min(bettercapacitylevels);
%             end;
%             % if the capacity is still not enough, then scale all flows down
%             if (Capacities(largestloaded) < Q(largestloaded))
%                 % calculate the multiplication factor
%                 factor = MAX_LINK_UTIL * Capacities(largestloaded) / Q(largestloaded);
%                 if (factor > 1) % this cannot happen
%                     factor
%                 end;
%                 % scale everybody down
%                 factor
%                 TVector = TVector .* factor;
%             end;
        end;
    end;

end;

if (INFEASIBLE_LINKS == 1)
    % find the largest load per link
    [t1,largestloaded] = max(Q);
    largestload = Q(largestloaded);
    largestloaded
    largestload
    
    if (capacitylevels(1) < largestload)
        % calculate the multiplication factor
        factor = MAX_LINK_UTIL * capacitylevels(1) / Q(largestloaded);
        if (factor > 1) % this cannot happen
            factor
        end;
        % scale everybody down
        factor
        TVector = TVector .* factor;
    end;

    %% nonzero traffic flows
    numofnonzeroflows = size(find(TVector));
    nonzeroflowspercentage = 100*numofnonzeroflows(1) / numofflows;
    nonzeroflowspercentage

    %% CALCULATE LOAD ON INDIVIDUAL LINKS
    Q = 0;
    Q = R' * TVector;

    for i=1:numoflinks
        Capacities(i) = max(Capacities(i) .* factor, capacitylevels(numofcapacitylevels));
    end;
    
    % check feasibility again -- in case
    feasible = 1;
    unfeasiblelinkscount = 0;
    overloads = 0;
    unfeasiblelinks = 0;
    for i=1:numoflinks
        if (Q(i) ./ Capacities(i) - MAX_LINK_UTIL > 0.01) %% +/- 1% error due to Matlab's precision issues
            feasible = 0;
            %Q(i)
            %Capacities(i)

            unfeasiblelinkscount = unfeasiblelinkscount + 1;
            unfeasiblelinks(unfeasiblelinkscount) = i;
            overloads(unfeasiblelinkscount) = Q(i) - Capacities(i);
        end;
    end;
    if (feasible == 0)
        feasible
        return;
    end;
end;

%return;

%% propagation delay of g2g paths
PathLatencies = zeros(numofflows,1);
for i=1:numofnodes
    for j=1:numofnodes
        if (i ~= j)
            flowid = (i-1)*numofnodes + j;
            PathLatencies(flowid) = sum(R(flowid,:)' .* latency);
        end;
    end;
end;
maxpathlatency = max(PathLatencies);
maxpathlatency

saveQ = Q;

ulevel = 0;
for u = urange
    ulevel = ulevel + 1;

    Q = 0;
    Q = saveQ*u;
    %% CALCULATE THE NETWORK'S UTILIZATION
    netutilization(ulevel) = 100*sum(Q) / sum(Capacities);
    netutilization(ulevel)

    %% CALCULATE THE LINK UTILIZATION
    linkutilization(ulevel) = 100*sum(Q ./ Capacities) / numoflinks;
    linkutilization(ulevel)

    %% CALCULATE PER-LINK EXCESS CAPACITY
    counter = 0;
    for E2E_p_avg = E2E_p_avg_range
        counter = counter + 1;
        E2E_p_avg

        p_avg = zeros(numoflinks,1);
        for i=1:numofnodes
            for j=1:numofnodes
                flowid = (i-1)*numofnodes + j;
                if (i ~= j  &&  TVector(flowid) > 0.0)
                    pathlength = sum(R(flowid,:));

                    %% go over all links this flow traverses
                    linkids = find(R(flowid,:));
                    [t1,t2] = size(linkids);
                    for k=1:t2
                        linkid = linkids(k);
                        current_p_avg = 1.0 - (1.0-E2E_p_avg/100.0)^(1.0/pathlength) ; %% 
                        current_p_avg = current_p_avg*100.0;

                        if (p_avg(linkid) > 0.0)
                            p_avg(linkid) = min( p_avg(linkid), current_p_avg );
                        else
                            p_avg(linkid) = current_p_avg;
                        end;
                    end;
                end;
            end;
        end;
        %t_avg

        %% sanity check for the t_avg values for the links
        for i=1:numoflinks
            if (Q(i) > 0 && p_avg(i) <= 0.0)
                Q(i)
                p_avg(i)
                return;
            end;
        end;

        gs = zeros(numoflinks,1);
        ExcessCapacities = zeros(numoflinks,1);
        for i=1:numoflinks
            if (Q(i) > 0) %% && t_avg(i) > 0)
                L_D = Q(i)*1000000.0 / (pkt_size*8.0); %% pkts/s
                if (TRAFFIC_MODEL == 1) %% M/M/1/K model %%% NOT USED NOW
%                     M_N = 1.0/t_avg(i) + L_D; 
%                     ExcessCapacities(i) = max(0, M_N*pkt_size*8.0 / 1000000.0 - Capacities(i)); %% Mb/s
%                     M_D = Capacities(i)*1000000.0 / (pkt_size*8.0); %% pkts/s
%                     rho = L_D / M_D;
%                     gs(i) = (1+ rho - M_D*t_avg(i)) / (rho - rho*M_D*t_avg(i));
                elseif (TRAFFIC_MODEL == 2) %% MMPP/M/1/K model
                    M_D = Capacities(i)*1000000.0 / (pkt_size*8.0); %% pkts/s
                    rho = L_D / M_D;
                    [rec, g] = getlinkmodelrecvalue(a_mmpp,r_mmpp,rho,p_avg(i),K);
                    M_N = M_D * (1 + rec/100.0);

                    ExcessCapacities(i) = max(0, M_N*pkt_size*8.0 / 1000000.0 - Capacities(i)); %% Mb/s
                    gs(i) = g;
                else %% LRD/D/1/K model
                    M_D = Capacities(i)*1000000.0 / (pkt_size*8.0); %% pkts/s
                    rho = L_D / M_D;
                    [rec, g] = getlrdlinkmodelrecvalue(Hurst,rho,p_avg(i),K);
                    M_N = M_D * (1 + rec/100.0);

                    ExcessCapacities(i) = max(0, M_N*pkt_size*8.0 / 1000000.0 - Capacities(i)); %% Mb/s
                    gs(i) = g;
                end;
            end;
        end;
        
%        allgs{counter,ulevel} = sum(cell2mat(gs))/numoflinks; % average g
        allgs{counter,ulevel} = gs;

        %% CALCULATE THE REQUIRED AGGREGATE NETWORK EXCESS CAPACITY
        aggregateexcesscapacity(counter,ulevel) = sum(ExcessCapacities);
        %        aggregateexcesscapacity(counter,ulevel)

        aggregateexcesspercentage(counter,ulevel) = 100 * aggregateexcesscapacity(counter,ulevel) / sum(Capacities(find(Q>0)));
        %        aggregateexcesspercentage(counter,ulevel)

        %% CALCULATE THE REQUIRED AVERAGE LINK EXCESS CAPACITY IN PERCENTAGE
        [t1,t2] = size(find(Q<=0));
        linkexcesscapacitypercentage(counter,ulevel) = 100.0 * sum(ExcessCapacities ./ Capacities) / (numoflinks-t1);
        %        linkexcesscapacitypercentage(counter,ulevel)
        
        % save the excess capacities
        allexcesscapacities{counter,ulevel} = ExcessCapacities;
        
        [n, t] = size(find(ExcessCapacities - Capacities));
        numofupdates{counter,ulevel} = n;
        
    end;
    linkexcesscapacitypercentage
    aggregateexcesspercentage
    
end;

%avggs = cell2mat(allgs);

for i=1:counter
    for j=1:ulevel
        avggs(i,j) = sum(min(allgs{i,j},1.0))/numoflinks;
    end;
end;
 
% record REC in two different ways
fname = ['../../results/isps/',ispname,'/rec-sum-of-ratios.txt'];
dlmwrite(fname, linkexcesscapacitypercentage, '-append', 'delimiter', ' ');
fname = ['../../results/isps/',ispname,'/rec-ratio-of-sums.txt'];
dlmwrite(fname, aggregateexcesspercentage, '-append', 'delimiter', ' ');
fname = ['../../results/isps/',ispname,'/numofupdates.txt'];
dlmwrite(fname, numofupdates, '-append', 'delimiter', ' ');

fname = ['../../results/isps/',ispname,'/avggs.txt'];
dlmwrite(fname, avggs, '-append', 'delimiter', ' ');

% record the Capacities before and after REC
fname = ['../../results/isps/',ispname,'/capacities.txt'];
dlmwrite(fname, Capacities, '-append', 'delimiter', ' ');
for i=1:counter
    for j=1:ulevel
        fname = ['../../results/isps/',ispname,'/excess-cap-',num2str(i),'-',num2str(j),'.txt'];
        dlmwrite(fname, allexcesscapacities{i,j}+Capacities, '-append', 'delimiter', ' ');
    end;
end;

% record the avg link utilizations
fname = ['../../results/isps/',ispname,'/avg-utilization.txt'];
dlmwrite(fname, linkutilization', '-append', 'delimiter', ' ');

%count = 0;
%icount = 0;
%for i=E2E_t_avg_range
%    icount = icount + 1;
%    for j=1:10
%        count = count + 1;
%        x(count) = i;
%        y(count) = linkutilization(j);
%        z(count) = linkexcesscapacitypercentage(icount,j);
%    end;
%end;

%%y = linkutilization;
%%x = E2E_t_avg_range;
%%z = linkexcesscapacitypercentage;

%grid on;
%tri = delaunay(x,y);
%%hold on, triplot(tri,x,y), hold off;
%hidden on;
%trimesh(tri,x,y,z,'LineWidth',1);
%grid on;

%%Thetarange = 0.1:5:170.1; 
%%Prange = 4:4:32; 
%%[XI,YI] = meshgrid(Thetarange,Prange);
%%ZI = griddata(x,y,z,XI,YI);
%%%Plot the gridded data along with the nonuniform data points used to generate it: 
%%mesh(XI,YI,ZI), hold

%ylabel('P -- Source Power (mW)', 'FontSize',12,'FontWeight','bold');
%xlabel('\theta -- Divergence Angle (mRad)', 'FontSize',12,'FontWeight','bold');
%zlabel('I -- Interference Area (m^2)', 'FontSize',12,'FontWeight','bold');

%%xlim([0.5,250]);
%%ylim([4,32]);
%currFig = get(0,'CurrentFigure');
%set(currFig,'Color',[1,1,1]);
