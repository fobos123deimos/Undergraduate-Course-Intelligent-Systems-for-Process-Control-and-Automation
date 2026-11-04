function y=neural_rollout(model,inputs,initial_output)
%NEURAL_ROLLOUT Recursive free run: only the initial output is measured.
inputs=inputs(:);assert(all(isfinite(inputs)) && isscalar(initial_output) && isfinite(initial_output));
y=zeros(numel(inputs)+1,1);y(1)=initial_output;
for k=1:numel(inputs),y(k+1)=neural_predict(model,[y(k) inputs(k)]);end
end
