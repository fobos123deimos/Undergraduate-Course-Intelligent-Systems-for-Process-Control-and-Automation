function results = validate_all()
%VALIDATE_ALL Run every curriculum laboratory without graphical windows.
results=cell(9,1);
for unit=1:9,results{unit}=run_lesson(unit,false);end
% Unit 03 must exercise the dynamic coupled plant, not only its static RGA.
structures=results{3}; expected=structures.gain_matrix\[.6;.65];
for name={'decentralized','decoupled'}
 response=structures.(name{1});
 assert(all(isfinite(response.states(:))) && all(isfinite(response.inputs(:))));
 assert(all(response.inputs(:)>=0 & response.inputs(:)<=1));
 assert(norm(response.states(end,:)'-[.6;.65],Inf)<.02);
 assert(norm(response.inputs(end,:)'-expected,Inf)<.02);
 assert(norm(response.states(1,:)'-structures.gain_matrix*[.3;.3],Inf)<1e-12);
end
assert(isequal(structures.decentralized.reference,structures.decoupled.reference));
assert(norm(structures.decentralized.states-structures.decoupled.states,'fro')>.01);
% Unit 05 must apply a derivative action as well as schedule proportional and
% integral gains. Compare with an otherwise identical fuzzy PI ablation.
fuzzy=results{5};
assert(all(fuzzy.fuzzy_pid.gains(:,3)>=0 & fuzzy.fuzzy_pid.gains(:,3)<=.1+eps));
assert(max(abs(fuzzy.fuzzy_pid.derivative_term))>1e-5);
assert(all(fuzzy.fuzzy_pi.gains(:,3)==0));
assert(norm(fuzzy.fuzzy_pid.u-fuzzy.fuzzy_pi.u,Inf)>1e-5);
assert(abs(fuzzy.fuzzy_pid.y(end)-.45)<.03);
validate_mpc();
% Neural free run must use its own output history after the initial sample.
neural=results{6};validation=neural.neural_validation;
assert(all(validation.ood_inputs(:,1)>1) && all(validation.ood_inputs(:,2)>1));
for family={'mlp','rbf'}
 name=family{1};record=validation.(name);model=neural.neural_models.(name);
 assert(record.free_run(1)==validation.truth(1));
 assert(all(isfinite([record.one_step;record.free_run;record.ood_prediction])));
 assert(abs(record.free_run(3)-neural_predict(model,[record.free_run(2) validation.inputs(2)]))<1e-12);
 assert(abs(record.one_step(2)-neural_predict(model,[validation.truth(2) validation.inputs(2)]))<1e-12);
 assert(norm(record.free_run(2:end)-record.one_step)>1e-5);
 assert(record.free_run_rmse>=0 && record.ood_rmse>=0);
end
assert(results{4}.siso.solver_failures==0 && results{4}.mimo.solver_failures==0);
fprintf('Neural one-step, recursive and out-of-domain validation checks passed.\n');
validate_markov();
validate_blending_tank();
fprintf('All nine laboratory units passed.\n');
end
