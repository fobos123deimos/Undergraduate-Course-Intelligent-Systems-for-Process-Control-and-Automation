function prediction = local_arx_predict(model,u,y,recursive)
%LOCAL_ARX_PREDICT Seed two samples; later recursion reads predictions only.
if nargin<4,recursive=false;end
u=u(:);y=y(:);assert(numel(u)==numel(y) && numel(y)>=3 && all(isfinite([u;y])));
prediction=y;
for k=3:numel(y)
 if recursive,history=prediction;else,history=y;end
 z=[history(k-1)-history(k-2) u(k-1)];
 w=local_arx_weights(model,(z-model.mean)./model.scale);
 phi=[history(k-1);history(k-2);u(k-1);1];
 prediction(k)=w*(model.coefficients*phi);
 if ~isfinite(prediction(k)),error('Recursive predictor diverged.');end
end
end
