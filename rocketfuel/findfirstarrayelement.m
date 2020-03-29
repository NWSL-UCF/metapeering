function [index] = findfirstarrayelement(Array,Key)
%% finds the first matching Key element of the Array of strings.
[m,n] = size(Array);
for j=1:m
    if strcmp(Key, Array(j))
        index = j;
        return;
    end;
end;
index = 0;
return;