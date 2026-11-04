function u=neural_inverse_action(model,reference,measurement)
%NEURAL_INVERSE_ACTION Unit06 bounded forward-model inversion by bisection.
% Monotonic behavior of the fitted model is a teaching-region assumption,
% not a general property of RBF networks or a global control guarantee.
assert(isscalar(reference)&&isscalar(measurement)&&all(isfinite([reference measurement])));
goal=measurement+.04*(reference-measurement);lo=0;hi=1;
for k=1:24
 mid=(lo+hi)/2;prediction=neural_predict(model,[measurement mid]);
 if prediction<goal,lo=mid;else,hi=mid;end
end
u=(lo+hi)/2;
end
