%% which topology to use
TOPOLOGY = 6;

FAILURE_TYPE = 2; % 1 -- link, 2 -- node

if (TOPOLOGY == 1) %% TELSTRA
    %% nodes 108, links 414, Telstra (Australia), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('1221/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1221/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 5;
    DISTANCETHRESH = 4;
    if (FAILURE_TYPE == 1)
        ispname = 'telstra';
    else
        ispname = 'telstra-nodes';
    end;
elseif (TOPOLOGY == 2) %% SPRINTLINK
    %% nodes 315, links 2339, Sprintlink (US), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('1239/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1239/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 9;
    DISTANCETHRESH = 5;
    if (FAILURE_TYPE == 1)
        ispname = 'sprintlink';
    else
        ispname = 'sprintlink-nodes';
    end;
elseif (TOPOLOGY == 3) %% EBONE
    %% nodes 87, links 407, Ebone (Europe), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('1755/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('1755/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 6;
    DISTANCETHRESH = 4;
    if (FAILURE_TYPE == 1)
        ispname = 'ebone';
    else
        ispname = 'ebone-nodes';
    end;
elseif (TOPOLOGY == 4) %% TISCALI
    %% nodes 161, links 900, Tiscali (Europe), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('3257/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('3257/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 8;
    DISTANCETHRESH = 4;
    if (FAILURE_TYPE == 1)
        ispname = 'tiscali';
    else
        ispname = 'tiscali-nodes';
    end;
elseif (TOPOLOGY == 5) %% EXODUS
    %% nodes 79, links 353, Exodus (US), BIDIRECTIONAL, CONNECTED
    [A, B, latency] = textread('3967/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('3967/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 6;
    DISTANCETHRESH = 4;
    if (FAILURE_TYPE == 1)
        ispname = 'exodus';
    else
        ispname = 'exodus-nodes';
    end;
elseif (TOPOLOGY == 6) %% ABOVENET
    %% nodes 141, links 925, Abovenet (US), BIDIRECTIONAL, DISCONNECTED
    [A, B, latency] = textread('6461/latencies.intra', '%s %s %f');
    [C, D, weight] = textread('6461/weights.intra', '%s %s %f');
    %% thresholds for edge node selection:
    DEGREETHRESH = 9;
    DISTANCETHRESH = 3;
    if (FAILURE_TYPE == 1)
        ispname = 'abovenet';
    else
        ispname = 'abovenet-nodes';
    end;
end;

[numoflinks,n] = size(A);

%failurecount = ceil(numoflinks*0.5) - 1;
failurecount = 33;

fname = ['../../results/isp-failures/',ispname,'/rec-0.txt'];
nofailurerec = dlmread(fname, ' ');
for i=1:failurecount
    fname = ['../../results/isp-failures/',ispname,'/additional-rec-',num2str(i),'.txt'];
    failurerecs{i} = dlmread(fname, ' ');
end;

% calculate the maximum recs 
for i=1:failurecount
    failurerecs{i} = nofailurerec + failurerecs{i};
end;

return;

maxfailurerec = nofailurerec;
for i=1:failurecount
    for col=1:10
        maxfailurerec(:,col) = max(maxfailurerec(:,col), failurerecs{i}(:,col));
    end;
end;

fname = ['../../results/isp-failures/',ispname,'/max-rec.txt'];
dlmwrite(fname, maxfailurerec, '-append', 'delimiter', ' ');

%exit;


% calculate and record the average additional RECs after each link failure
for j=1:failurecount
    totalextrarec = 0;
    for i=1:j
        totalextrarec = totalextrarec + max(0,failurerecs{i});
    end;
    avgextrarec = totalextrarec ./ j;

    fname = ['../../results/isp-failures/',ispname,'/avg-additional-rec-',num2str(j),'.txt'];
    dlmwrite(fname, avgextrarec, '-append', 'delimiter', ' ');
end;

% read the link utilizations after each failure
fname = ['../../results/isp-failures/',ispname,'/rec-0.txt'];
nofailurerec = dlmread(fname, ' ');
for i=0:failurecount
    fname = ['../../results/isp-failures/',ispname,'/link-utilizations-',num2str(i),'.txt'];
    individuallinkutilizations{i+1} = dlmread(fname, ' ');
end;

% record the max, min, and average link utilizations after each failure
for i=0:failurecount
    maxlinkutilizations(i+1) = max(individuallinkutilizations{i+1});
    minlinkutilizations(i+1) = min(individuallinkutilizations{i+1});
    avglinkutilizations(i+1) = mean(individuallinkutilizations{i+1});
end;
fname = ['../../results/isp-failures/',ispname,'/max-link-utilizations-.txt'];
dlmwrite(fname, maxlinkutilizations, '-append', 'delimiter', '\n');
fname = ['../../results/isp-failures/',ispname,'/min-link-utilizations-.txt'];
dlmwrite(fname, minlinkutilizations, '-append', 'delimiter', '\n');
fname = ['../../results/isp-failures/',ispname,'/avg-link-utilizations-.txt'];
dlmwrite(fname, avglinkutilizations, '-append', 'delimiter', '\n');





% ispname = 'exodus';
% fname = ['../../results/isp-failures/',ispname,'/rec-0.txt'];
% x = dlmread(fname, ' ');
% for i=1:35
%     fname = ['../../results/isp-failures/',ispname,'/additional-rec-',num2str(i),'.txt'];
%     y = dlmread(fname, ' ');
%     fname = ['../../results/isp-failures/',ispname,'/xadditional-rec-',num2str(i),'.txt'];
%     dlmwrite(fname, y-x, '-append', 'delimiter', ' ');
% end;

%%%%%%%%%%%%%%%%%%%%%%%%% VARIOUS STUFF
fname = ['../../results/isps/',ispname,'/Capacities.txt'];
Capacities = dlmread(fname, ' ');
fname = ['../../results/isps/',ispname,'/excess-cap-1-1.txt'];
ExcessCapacities = dlmread(fname, ' ');

for i=1:counter
    for j=1:ulevel
        fname = ['../../results/isps/',ispname,'/excess-cap-',num2str(i),'-',num2str(j),'.txt'];
        ExcessCapacities = dlmread(fname, ' ');
        [n, t] = size(find(ExcessCapacities - Capacities));
        numofupdates{i,j} = n;
    end;
end;



fname = ['../../results/isp-failures/',ispname,'/capacities.txt'];
Capacities = dlmread(fname, ' ');
for k=1:failurecount
    for i=1:counter
        for j=1:ulevel
            fname = ['../../results/isp-failures/',ispname,'/excess-cap-',num2str(k),'-',num2str(i),'-',num2str(j),'.txt'];
            ExcessCapacities = dlmread(fname, ' ');
            [n, t] = size(find(ExcessCapacities - Capacities));
            numofupdates{i,j,k} = n;
        end;
    end;
end;

