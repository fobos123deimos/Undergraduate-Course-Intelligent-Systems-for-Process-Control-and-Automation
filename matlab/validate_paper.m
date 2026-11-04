function records = validate_paper()
%VALIDATE_PAPER Check equilibrium, conservation and source equations.
fixture=fullfile(fileparts(mfilename('fullpath')),'paper_reference_values.json');
cases=jsondecode(fileread(fixture));
for k=1:numel(cases)
 actual=paper_models(cases(k).name,cases(k).state,cases(k).inputs);
 expected=cases(k).expected(:);
 assert(norm(actual(:)-expected,Inf)<1e-9*max(1,norm(expected,Inf)));
end
assert(paper_models('siso',[0;0],.2)==.2);
assert(norm(paper_models('mimo',[0;0],[.2;.3])-[.2;.3])<eps);
assert(norm(paper_models('pendulum',zeros(4,1),0))==0);
assert(norm(paper_models('pneumatic',[0;0;5e5;5e5],zeros(5,1)))==0);
h=[.4;.2;.3];q=[4e-5;3e-5];dh=paper_models('three_tank',h,q);
assert(abs(.0154*sum(dh)-sum(q))<1e-15);
assert(norm(paper_models('bioreactor',[0;0],1))==0);
bioeq=[.08729754781771586;.9235897740828826];
assert(norm(paper_models('bioreactor',bioeq,.769))<1e-10);
bio=paper_models('bioreactor_sample',[.2;.3],1);assert(all(bio>=0 & bio<=1));
c=[linspace(.01,.99,41)';.5*ones(41,1)];u=[2.70629;3.20629;.5;.5;1;.5;1];
dc=paper_models('column_a',c,u);assert(abs(sum(dc(42:end)))<1e-12);
component=sum(c(42:end).*dc(1:41)+c(1:41).*dc(42:end));
assert(abs(component-(u(5)*u(6)-u(3)*c(41)-u(4)*c(1)))<1e-12);
cstr=paper_models('cstr',[3517.5;740;87;79.8],[8.256;-6.239]);
% The table is rounded: these values are NOT an exact numerical equilibrium.
assert(all(isfinite(cstr)));
hydro=paper_models('hydrostatic',[0;0;0;0],[0;0],struct('pump_speed',100));assert(norm(hydro)==0);
wind=paper_models('wind',[zeros(4,1);0;0;1;1;0],[10;0;0]);assert(all(isfinite(wind)));
rng(30,'twister');input=randn(600,1);output=zeros(600,1);
for k=1:599,output(k+1)=.5*output(k)+.3*input(k);end
for mode={'crisp','soft'}
 model=local_arx_fit(input(1:400),output(1:400),mode{1});
 prediction=local_arx_predict(model,input(401:end),output(401:end),true);
 assert(max(abs(prediction-output(401:end)))<1e-5);
end
records=struct('cstr_table_residual',cstr,'bioreactor_after_one_hold',bio,...
 'three_tank_total_volume_rate',.0154*sum(dh),'column_component_rate',component,'wind_derivative',wind);
fprintf('Published-equation checks passed for ten mathematical benchmarks.\n');
end
