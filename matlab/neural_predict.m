function y=neural_predict(model,X)
%NEURAL_PREDICT Evaluate a fixed Unit06 model without fitting on evaluation data.
assert(isnumeric(X) && size(X,2)==2 && all(isfinite(X(:))),'Finite [previous output,input] rows required');
switch model.kind
 case 'mlp'
  hidden=tanh([ones(size(X,1),1) X]*model.W1);
  y=[ones(size(X,1),1) hidden]*model.W2;
 case 'rbf'
  Phi=ones(size(X,1),size(model.centers,1)+1);
  for j=1:size(model.centers,1)
   Phi(:,j+1)=exp(-sum((X-model.centers(j,:)).^2,2)/(2*model.width^2));
  end
  y=Phi*model.weights;
 otherwise,error('Unknown neural model kind');
end
assert(all(isfinite(y(:))),'Neural prediction is nonfinite');
end
