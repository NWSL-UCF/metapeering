%% FIGURE OUT WHY T_AVG AND Q DO NOT MATCH

%% end-to-end delay requirement for premium class traffic (milliseconds)
E2E_t_avg_range = 106:1:150;

N_q_mintavg = 1.0;

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
[connected, TC] = TestConnectivity(Adj);
connected
%%[Connectivity, NumofComponents, GlobalRoot, GlobalParent, GlobalCycle]=Dfs(Adj)
%% FIX IF THERE ARE DISJOINT SUBSETS
if (~connected) %% HERE: currently we are just exiting instead of fixing
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

%% CALCULATE THE ALL PAIRS SHORTEST PATH
%% Floyd-Warshall algorithm
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

%% make BFS starting from the maxdegree node
[maxdegree,maxindices] = max(Degrees);
[Distance,Parent,Layers,NumofLayers]= Bfs(Adj,maxindices(1));
%Distance
%Parent

%% assign capacities to the links (in Mb/s)
capacitylevels = [10000, 2500, 620, 155, 45, 10, 1.5, 1.0];
Capacities = zeros(numoflinks,1);
for i=1:numoflinks
    xid = findfirstarrayelement(routers,A(i));
    yid = findfirstarrayelement(routers,B(i));
    maxdistance = max(Distance(xid),Distance(yid));
    Capacities(i) = capacitylevels(maxdistance);
end;
%Capacities

%% FORM THE TRAFFIC VECTOR FROM THE TRAFFIC MATRIX
%% HERE: need to have a realistic traffic matrix
TVector = zeros(numofflows,1);
for i=1:numofnodes
    for j=1:numofnodes
        %% Need to identify edge routers
        %% assumption: edge routers have either degree < 3 or distance > 4
        %% old assumption: each edge-to-edge flow is 0.23Mb/s for Exodus
        %% old assumption: each edge-to-edge flow is 0.0095Mb/s for Ebone
        if (i ~= j)
            if (Degrees(i) < 3  ||  Distance(i) > 4)
                if (Degrees(j) < 3  ||  Distance(j) > 4)
                    flowid = (i-1)*numofnodes + j;
                    % assign min capacity of all links the flow is
                    % traversing
                    % TVector(flowid) = 0.23;
                    % need to multiply by 0.95 or something
                    TVector(flowid) = 0.95*min(Capacities(find(R(flowid,:))));
                end;
            end;
        end;
    end;
end;
%TVector

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
        if (Q(i) / Capacities(i) > 0.95) %% limit link utilization by 95%
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
        % calculate the multiplication factor
        factor = Capacities(mostoverloaded) / Q(mostoverloaded)
        %        if (Capacities(mostoverloaded) / Q(mostoverloaded) > 0.95)
        if (factor > 0.95)
            factor = 0.95
        end;
        % find flows traversing this link
        traversingflows = 0;
        traversingflows = find(R(:,mostoverloaded));
        
        extra = Q(mostoverloaded) - 0.95*Capacities(mostoverloaded);
        while (extra > 0)
            [C1, C1_ind] = max(TVector(traversingflows));
            Cprime = sum(TVector(traversingflows)) - C1;
            C1_f_ind = traversingflows(C1_ind);
            if (Cprime == 0  ||  C1-Cprime >= extra)
                TVector(C1_f_ind) = TVector(C1_f_ind) - extra;
                extra = 0;
            else
                TVector(C1_f_ind) = (C1 + Cprime - extra) / 2.0;
                extra = extra - (C1 - TVector(C1_f_ind));
            end;
            if (extra < 0  ||  TVector(C1_f_ind) < 0)
                extra
                TVector(C1_f_ind)
                return;
            end;
            traversingflows(C1_ind,:) = []; % delete the max rate flow from the set of traversing flows
        end;
        
    end;

end;

%% CALCULATE THE NETWORK'S UTILIZATION
netutilization = 100*sum(Q) / sum(Capacities);
netutilization

%% CALCULATE THE LINK UTILIZATION
linkutilization = 100*sum(Q ./ Capacities) / numoflinks;
linkutilization

%% CALCULATE PER-LINK EXCESS CAPACITY
pkt_size = 1024 %% bytes

%% HERE: SLA requirement for individual links
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

counter = 0;
for E2E_t_avg = E2E_t_avg_range
    counter = counter + 1;
    E2E_t_avg

    unsatisfiedSLA(counter) = 0;
    
    t_avg = zeros(numoflinks,1);
    min_t_avg = zeros(numoflinks,1);
    for i=1:numofnodes
        for j=1:numofnodes
            flowid = (i-1)*numofnodes + j;
            if (i ~= j  &&  TVector(flowid) > 0.0)
                pathlength = sum(R(flowid,:));
                pathlatency = sum(R(flowid,:)' .* latency);
                leftlatency = E2E_t_avg - pathlatency;

                if (leftlatency <= 0.0) %% unsatisfied g2g flow
                    unsatisfiedSLA(counter) = unsatisfiedSLA(counter) + 1;
                end;

                %% go over all links this flow traverses
                linkids = find(R(flowid,:));
                [t1,t2] = size(linkids);
                for k=1:t2
                    linkid = linkids(k);
                    M_D = Capacities(linkid)*1000000.0 / (pkt_size*8.0); %% pkts/s
                    %                min_t_avg = 1.05 * 1.0/M_D; %% min possible t_avg for this link
                    %% HERE HERE: change the (x + 1.0) / M_D below to reduce the
                    %% effect of unsatisfied flows    
                    min_t_avg(linkid) = 1000.0 * ( N_q_mintavg + 1.0)/M_D; %% min possible t_avg for this link (milliseconds)

                    if (leftlatency <= 0.0) %% unsatisfied g2g flow
                        current_t_avg = min_t_avg(linkid);
                    else
                        current_t_avg = max( min_t_avg(linkid), leftlatency/(pathlength) ); %% milliseconds
                    end;

                    if (t_avg(linkid) > 0.0)
                        t_avg(linkid) = min( t_avg(linkid), current_t_avg );
                    else
                        t_avg(linkid) = current_t_avg;
                    end;                
                    t_avg(linkid) = max( min_t_avg(linkid), t_avg(linkid) );
                end;
            end;
        end;
    end;
    %t_avg
    
    unsatisfiedSLA(counter) = 100*unsatisfiedSLA(counter)/numofnonzeroflows(1);
    unsatisfiedSLA(counter);

    %% sanity check for the t_avg values for the links
    for i=1:numoflinks
        if (Q(i) > 0 && t_avg(i) <= 0.0)
            Q(i)
            t_avg(i)
            return;
        end;
    end;

    t_avg = t_avg * 0.001; %% convert to seconds

    ExcessCapacities = zeros(numoflinks,1);
    for i=1:numoflinks
        if (Q(i) > 0) %% && t_avg(i) > 0)
            L_D = Q(i)*1000000.0 / (pkt_size*8.0); %% pkts/s
%            M_N = 1.0/t_avg(i) + L_D; %% M/M/1 model
            M_N = 0.5/t_avg(i) + 1.25*L_D + sqrt(9.0*L_D^2/16.0 - 0.25*L_D/t_avg(i) + 0.25/t_avg(i)^2 ) ; %% MMPP/M/1 model
            ExcessCapacities(i) = max(0, M_N*pkt_size*8.0 / 1000000.0 - Capacities(i)); %% Mb/s 
        end;
    end;

    %% CALCULATE THE REQUIRED AGGREGATE NETWORK EXCESS CAPACITY
    aggregateexcesscapacity(counter) = sum(ExcessCapacities);
    aggregateexcesscapacity(counter)

    aggregateexcesspercentage(counter) = 100 * aggregateexcesscapacity(counter) / sum(Capacities);
    aggregateexcesspercentage(counter)

    %% CALCULATE THE REQUIRED AVERAGE LINK EXCESS CAPACITY IN PERCENTAGE
    linkexcesscapacitypercentage(counter) = 100.0 * sum(ExcessCapacities ./ Capacities) / numoflinks;
    linkexcesscapacitypercentage(counter)

end;