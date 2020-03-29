% Sketch of |X(s)|, where X(s)=1/(s+a)(s+b)
%[LD, tavg, model_tavg] = textread('sysdelays-aggregate-muD=8.192', '%f %f %f');

%% nodes 108, links 306, Telstra (Australia), BIDIRECTIONAL, DISCONNECTED
%[A, B, latency] = textread('1221/latencies.intra', '%s %s %f');
%[C, D, weight] = textread('1221/weights.intra', '%s %s %f');
%% nodes 315, links 1944, Sprintlink (US), BIDIRECTIONAL, DISCONNECTED
%[A, B, latency] = textread('1239/latencies.intra', '%s %s %f');
%[C, D, weight] = textread('1239/weights.intra', '%s %s %f');
%% nodes 87, links 322, Ebone (Europe), BIDIRECTIONAL, CONNECTED
%[A, B, latency] = textread('1755/latencies.intra', '%s %s %f');
%[C, D, weight] = textread('1755/weights.intra', '%s %s %f');
%% nodes 161, links 656, Tiscali (Europe), BIDIRECTIONAL, CONNECTED
%[A, B, latency] = textread('3257/latencies.intra', '%s %s %f');
%[C, D, weight] = textread('3257/weights.intra', '%s %s %f');
%% nodes 79, links 294, Exodus (US), BIDIRECTIONAL, CONNECTED
[A, B, latency] = textread('3967/latencies.intra', '%s %s %f');
[C, D, weight] = textread('3967/weights.intra', '%s %s %f');
%% nodes 141, links 748, Abovenet (US), BIDIRECTIONAL, DISCONNECTED
%[A, B, latency] = textread('6461/latencies.intra', '%s %s %f');
%[C, D, weight] = textread('6461/weights.intra', '%s %s %f');

[numoflinks,n] = size(A);

%A
%B
%latency
% CHECK IF THE LATENCY AND WEIGHTS DATA MATCH
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
%for i=1:numoflinks
%    Adj(i,i) = 1;
%end;
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
%    Adj(y,x) = 1;
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
[connected, TC] = TestConnectivity(Adj);
connected
%%[Connectivity, NumofComponents, GlobalRoot, GlobalParent, GlobalCycle]=Dfs(Adj)
%% FIX IF THERE ARE DISJOINT SUBSETS
if (~connected) %% currently we are just exiting instead of fixing
    return;
end;
 
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

%% CALCULATE THE ALL PAIRS SHORTEST PATH -- Floyd-Warshall algorithm
[SP, Prev] = AllPairsShortestPath(Cost);

%% CONSTRUCT THE ROUTING MATRIX
numofflows = numofnodes*numofnodes;
R = zeros(numofflows,numoflinks);
% for all flows..
for i=1:numofnodes
    for j=1:numofnodes
        if (i ~= j)
            flowid = (i-1)*numofnodes + j;
            introuter = Prev(i,j);
            last = j;
            % mark all the links this flow is passing through
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
            end;
            % don't forget the very first link this flow traverses
            linkid = findlink(routers(introuter),routers(last),A,B);    
            R(flowid,linkid) = 1;
        end;
    end;
end;

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
[maxdegree,maxindices] = max(Degrees);
%maxdegree
%maxindices
%% make BFS starting from the maxdegree node
[Distance,Parent,Layers,NumofLayers]= Bfs(Adj,maxindices(1));
Distance
Parent
%% assign capacities to the links (in Mb/s)
capacitylevels = [10000, 2500, 620, 155, 45, 10, 1.5];
Capacities = zeros(numoflinks,1);
for i=1:numoflinks
    xid = findfirstarrayelement(routers,A(i));
    yid = findfirstarrayelement(routers,B(i));
    maxdistance = max(Distance(xid),Distance(yid));
    Capacities(i) = capacitylevels(maxdistance);
end;
Capacities

%% FORM THE TRAFFIC VECTOR FROM THE TRAFFIC MATRIX
%% HERE: need to have a realistic traffic matrix 
TVector = zeros(numofflows,1);
for i=1:numofnodes
    for j=1:numofnodes
        %% HERE: need to identify edge routers 
        %% assumption: edge routers have either degree < 3 or distance > 4
        %% assumption: each edge-to-edge flow is 0.18Mb/s
        if (i ~= j)
            if (Degrees(i) < 3  ||  Distance(i) > 4)
                if (Degrees(j) < 3  ||  Distance(j) > 3)
                    flowid = (i-1)*numofnodes + j;
                    TVector(flowid) = 0.18;
                end;
            end;
        end;
    end;
end;
%TVector

%% CALCULATE LOAD ON INDIVIDUAL LINKS
Q = R' * TVector;
Q

%% CHECK FEASIBILITY
for i=1:numoflinks
    if (Q(i) >= Capacities(i))
        Q(i)
        Capacities(i)
        return;
    end;
end;

%% IF NOT FEASIBLE, EITHER REVISE THE TRAFFIC MATRIX OR THE ROUTING MATRIX
%% HERE: need to implement this

%% CALCULATE THE NETWORK'S UTILIZATION
netutilization = 100*sum(Q) / sum(Capacities);
netutilization

%% CALCULATE PER-LINK EXCESS CAPACITY
pkt_size = 1024 %% bytes

%% HERE: SLA requirement
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

E2E_t_avg = 110.0; %% milliseconds

t_avg = zeros(numoflinks,1);
for i=1:numofnodes
    for j=1:numofnodes
        if (i ~= j)
            flowid = (i-1)*numofnodes + j;
            pathlength = sum(R(flowid,:));
            pathlatency = sum(R(flowid,:)' .* latency);
            leftlatency = E2E_t_avg - pathlatency;
            
            linkids = find(R(flowid,:));
            [t1,t2] = size(linkids);
            for k=1:t2
                linkid = linkids(k);
                M_D = Capacities(linkid)*1000000.0 / (pkt_size*8.0); %% pkts/s
%                min_t_avg = 1.05 * 1.0/M_D; %% min possible t_avg for this link
                min_t_avg = 1000.0 * 1.05/M_D; %% min possible t_avg for this link (milliseconds)
            
                if (leftlatency <= 0.0)
                    current_t_avg = min_t_avg;
                else
                    current_t_avg = max( min_t_avg, leftlatency/(pathlength) ); %% milliseconds
                end;
                
                if (t_avg(linkid) > 0)
                    t_avg(linkid) = min( t_avg(linkid), current_t_avg );
                else
                    t_avg(linkid) = current_t_avg;
                end;
                
                if (t_avg(linkid) == 0)
                    t_avg(linkid)
                    return;
                end;
            end;
        end;
    end;
end;
t_avg

t_avg = t_avg * 0.001; %% seconds

%% sanity check for the t_avg values for the links
for i=1:numoflinks
    if (Q(i) < 0 && t_avg(i) <= 0)
        Q(i)
        t_avg(i)
        return;
    end;
end;


%t_avg = zeros(numoflinks,1);
%for i=1:numoflinks
%    if (latency(i) >= 2.0)
%        M_D = Capacities(i)*1000000.0 / (pkt_size*8.0); %% pkts/s
%        t_avg(i) = 1.05 * 1.0/M_D;
%    else
%        t_avg(i) = (2.0-latency(i)) / 1000.0; %% seconds
%    end;
%end;

ExcessCapacities = zeros(numoflinks,1);
for i=1:numoflinks
    if (Q(i) > 0) %% && t_avg(i) > 0)
        L_D = Q(i)*1000000.0 / (pkt_size*8.0); %% pkts/s
%        M_N = 1.0/t_avg(i) + L_D; %% M/M/1 model
        M_N = 0.5/t_avg(i) + 1.25*L_D/t_avg(i) + sqrt(9.0*L_D^2/16.0 - 0.25*L_D/t_avg(i) + 0.25/t_avg(i)^2 ) ; %% MMPP/M/1 model
        ExcessCapacities(i) = max(0, M_N*pkt_size*8.0 / 1000000.0 - Q(i)); %% Mb/s 
    end;
end;

%% CALCULATE THE REQUIRED AGGREGATE NETWORK EXCESS CAPACITY
aggregateexcesscapacity = sum(ExcessCapacities);
aggregateexcesscapacity

aggregateexcesspercentage = 100 * aggregateexcesscapacity / sum(Capacities);
aggregateexcesspercentage
