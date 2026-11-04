function weights = local_arx_weights(model,z)
%LOCAL_ARX_WEIGHTS Partition weights for standardized feature rows.
n=size(z,1);rules=size(model.centers,1);dist=zeros(n,rules);
for j=1:rules,dist(:,j)=sum((z-model.centers(j,:)).^2,2);end
if strcmp(model.mode,'crisp')
 [~,labels]=min(dist,[],2);weights=zeros(n,rules);
 for k=1:n,weights(k,labels(k))=1;end
else
 weights=1./max(dist,1e-12);weights=weights./sum(weights,2);
end
end
