function report=validate_wind_control()
%VALIDATE_WIND_CONTROL CARE, equilibrium, scheduling and nonlinear trajectory.
points=wind_control('design');
for k=1:3
 p=points(k);assert(norm(wind_control('rhs',p.state,p.command,p.wind),Inf)<1e-9);
 assert(p.max_pole_real<-1e-4&&p.care_residual<1e-5);
end
for v=12:.25:16
 h=wind_control('weights',v,points);assert(all(h>=0)&&abs(sum(h)-1)<eps*4);
 p=wind_control('equilibrium',v);s=wind_control('linearize',p.state,p.command,v);K=zeros(2,8);
 for k=1:3,K=K+h(k)*points(k).gain;end
 assert(max(real(eig(s.A-s.B*K)))<0);
end
result=run_wind_control(true,60,.02,points);u=result.command;
assert(all(all(u>=[0 0]))&&all(all(u<=[6e6 30*pi/180])));
assert(all(all(abs(diff(u))<=[5e5 8*pi/180]*.02+1e-8)));
assert(abs(result.state(end,6)-1.2)<.01&&result.speed_peak_error<.2);
fine=run_wind_control(true,24,.01,points);coarse=run_wind_control(true,24,.02,points);
assert(abs(fine.speed_rmse-coarse.speed_rmse)<.002&&abs(fine.state(end,6)-coarse.state(end,6))<.002);
% Independent cross-language fixture uses declared coordinates and units.
file=fullfile(fileparts(mfilename('fullpath')),'wind_control_reference.json');
ref=jsondecode(fileread(file));
for k=1:3
 assert(norm(points(k).state-ref.points(k).state(:),Inf)<1e-8);
 expected=ref.points(k).gain;assert(norm((points(k).gain-expected)./[1e6;1],Inf)<1e-4);
end
assert(abs(result.speed_rmse-ref.speed_rmse)<1e-5);
p=points(2);assert(norm(wind_control('variant',p.state([3 6 7 8]),p.command,14,'rigid_structure'),Inf)<1e-9);
target=p.command;target(2)=target(2)+.01;
[~,trajectory]=ode45(@(t,x)wind_control('variant',x,target,14,'second_order_pitch'),[0 1],[p.state;0],odeset('RelTol',1e-9,'AbsTol',1e-11));
assert(abs(trajectory(end,8)-(p.state(8)+.01*(1-11*exp(-10))))<1e-9);
report=struct('passed',true,'operating_points',3,'speed_rmse',result.speed_rmse,...
 'speed_peak_error',result.speed_peak_error,'local_poles',[points.max_pole_real],...
 'map_variant','ROSCO 2022; new LQR/PDC study, not published gains');
fprintf('Wind LQR/PDC equilibrium, scheduling, nonlinear limits and convergence checks passed.\n');
end
