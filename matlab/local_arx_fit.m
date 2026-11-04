function model = local_arx_fit(u,y,mode,rules)
%LOCAL_ARX_FIT Eight-local-model architecture for throttle identification.
% Training-only normalized partitions, nearest-center PWA or soft TS blend.
% This is an explicit teaching fit, not unavailable published coefficients.
if nargin<3,mode='soft';end
if nargin<4,rules=8;end
u=u(:);y=y(:);n=numel(y);ridge=1e-8;
assert(numel(u)==n && n>=max(20,5*rules) && all(isfinite([u;y])));
assert(any(strcmp(mode,{'soft','crisp'})) && rules>=1);
phi=[y(2:end-1) y(1:end-2) u(2:end-1) ones(n-2,1)];
z=[y(2:end-1)-y(1:end-2) u(2:end-1)];
model.mean=mean(z,1);model.scale=max(std(z,1,1),1e-12);model.mode=mode;
z=(z-model.mean)./model.scale;rng(2014,'twister');order=randperm(size(z,1));model.centers=z(order(1:rules),:);
for k=1:50
 dist=zeros(size(z,1),rules);
 for j=1:rules,dist(:,j)=sum((z-model.centers(j,:)).^2,2);end
 [~,labels]=min(dist,[],2);old=model.centers;
 for j=1:rules,if any(labels==j),model.centers(j,:)=mean(z(labels==j,:),1);end,end
 if max(abs(old(:)-model.centers(:)))<1e-10,break;end
end
w=local_arx_weights(model,z);globalfit=(phi'*phi+ridge*eye(4))\(phi'*y(3:end));model.coefficients=zeros(rules,4);
for j=1:rules
 if sum(w(:,j)>1e-12)>=4
  coef=(phi'*(w(:,j).*phi)+ridge*eye(4))\(phi'*(w(:,j).*y(3:end)));
 else,coef=globalfit;
 end
 model.coefficients(j,:)=coef';
end
end
