function values=alstom_log_matrix(raw,samples,channels,label)
%ALSTOM_LOG_MATRIX Normalize documented To Workspace vector/matrix layouts.
% Matrix signals log time on dimension three; vector signals log time first.
assert(isnumeric(raw)&&isreal(raw)&&all(isfinite(raw(:))),'Invalid %s log',label);
if isequal(size(raw),[samples channels])
 values=raw;
elseif ndims(raw)==3 && size(raw,3)==samples && ...
 ((size(raw,1)==channels&&size(raw,2)==1)||(size(raw,1)==1&&size(raw,2)==channels))
 values=reshape(raw,channels,samples)';
else
 error('ALSTOM:LogShape','Unexpected %s dimensions %s; expected %d samples and %d channels.',...
  label,mat2str(size(raw)),samples,channels);
end
end
