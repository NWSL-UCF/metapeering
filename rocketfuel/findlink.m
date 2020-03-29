function [index] = findlink(router1,router2,Alinks,Blinks)
%% finds the first matching link in the Key element of the Array of strings.
[m,n] = size(Alinks);
for j=1:m
    if ( strcmp(router1,Alinks(j)) && strcmp(router2,Blinks(j)) )
        index = j;
        return;
    end;
end;
index = 0;
return;