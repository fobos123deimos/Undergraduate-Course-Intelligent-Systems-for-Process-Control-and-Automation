function report=validate_pneumatic_physical(output_path)
%VALIDATE_PNEUMATIC_PHYSICAL Conservation, choking and cross-language traces.
p=pneumatic_physical('parameters');R=p.universal_R/p.air_molar_mass;cv=R/(p.gamma-1);cp=p.gamma*cv;
assert(abs(R-287.058)<.001&&abs(cp-cv-R)<1e-10);
assert(abs(p.midpoint_volume-p.area*p.half_stroke-1.5e-4)<1e-15);
heated=p;heated.wall_conductance=.2;heated.wall_temperature=313.15;
xe=pneumatic_physical('equilibrium',0,5e5,heated);
assert(all(xe(5:6)==313.15)&&norm(pneumatic_physical('rhs',xe,0,heated),Inf)<1e-10);
invalid=false;try,pneumatic_physical('observe',xe+[.01i;0;0;0;0;0],heated);catch,invalid=true;end
assert(invalid,'Complex states must be rejected.');
g=p.gamma;critical=(2/(g+1))^(g/(g-1));area=1e-6;up=9e5;T=293.15;
expected=p.discharge_coefficient*area*up/sqrt(T)*sqrt(g/R)*((g+1)/2)^(-(g+1)/(2*(g-1)));
q=pneumatic_physical('orifice',up,1e5,T,T,area,p);
assert(abs(q-expected)<1e-14&&abs(pneumatic_physical('orifice',up,2e5,T,T,area,p)-q)<1e-14);
assert(abs(pneumatic_physical('orifice',1e5,up,T,T,area,p)+q)<1e-14);
qa=pneumatic_physical('orifice',up,up*critical*(1-1e-8),T,T,area,p);
qb=pneumatic_physical('orifice',up,up*critical*(1+1e-8),T,T,area,p);assert(abs(qa-qb)<1e-14);

pc=p;pc.bypass_area=1e-8;pc.wall_conductance=.2;
x=pneumatic_physical('state',.02,.03,[6e5;4e5],[305;285],pc);
conservation_error=0;
for u=[-.7 .7]
 [dx,info]=pneumatic_physical('balances',x,u,pc,3);q=info.mass_flows;
 assert(abs(sum(dx(3:4))-(q(2)+q(3)-q(1)-q(4)))<1e-15);
 Udot=cv*(x(5:6).*dx(3:4)+x(3:4).*dx(5:6));
 source=cp*(pc.reservoir_temperature*(q(2)+q(3))-x(5)*q(1)-x(6)*q(4));
 M=p.piston_mass+p.load_mass;total=sum(Udot)+M*x(2)*dx(2)+M*p.gravity*x(2);
 residual=abs(total-source-sum(info.heat_rate)+info.friction*x(2)+3*x(2));
 conservation_error=max(conservation_error,residual);assert(residual<1e-10);
end

pc=p;pc.bypass_area=2e-7;x=pneumatic_physical('state',0,0,[7e5;3e5],[320;270],pc);
[dx,info]=pneumatic_physical('balances',x,0,pc);
assert(info.mass_flows(5)>0&&abs(sum(dx(3:4)))<1e-16);
assert(abs(sum(cv*(x(5:6).*dx(3:4)+x(3:4).*dx(5:6))))<1e-10);

pc=p;pc.viscous=0;pc.coulomb=0;pc.gravity=0;
x=pneumatic_physical('state',0,.03,[5e5;5e5],[293.15;293.15],pc);
sealed=pneumatic_physical('simulate',@(t)0,x,pc,.3,151);invariant=zeros(151,2);energy=zeros(151,1);
for j=1:151
 x=sealed.state(j,:)';[pressure,volume]=pneumatic_physical('observe',x,pc);
 invariant(j,:)=(pressure.*volume.^p.gamma)';energy(j)=sum(cv*x(3:4).*x(5:6))+.5*(pc.load_mass+pc.piston_mass)*x(2)^2;
end
ratio=bsxfun(@rdivide,invariant,invariant(1,:));adiabatic_error=max(abs(ratio(:)-1));
assert(adiabatic_error<2e-8&&max(abs(energy/energy(1)-1))<2e-9);

path=fullfile(fileparts(mfilename('fullpath')),'pneumatic_reference.json');reference=jsondecode(fileread(path));
errors=zeros(3,1);scale=[.125 1 .01 .01 300 300];
for j=1:3
 pc=p;pc.load_mass=reference.cases(j).load_kg;x=pneumatic_physical('equilibrium',0,5e5,pc);
 assert(norm(pneumatic_physical('rhs',x,0,pc),Inf)<1e-10);
 result=pneumatic_physical('simulate',@(t)2*sin(2*pi*t),x,pc,2,201);
 assert(max(abs(result.time-reference.cases(j).time))<1e-12);
 difference=bsxfun(@rdivide,result.state-reference.cases(j).state,scale);
 errors(j)=max(abs(difference(:)));assert(errors(j)<2e-6,'Independent solver trajectory mismatch.');
 local=pneumatic_physical('local',reference.local_models(j).index);
 assert(norm(local.A-reference.local_models(j).A,Inf)<1e-12);
 assert(norm(local.B-reference.local_models(j).B,Inf)<1e-10);
end
invalid=false;try,pneumatic_physical('state',.126,0,[5e5;5e5],[293.15;293.15],p);catch,invalid=true;end
assert(invalid,'Out-of-stroke state must be rejected.');
report=struct('runtime',version,'conservation_max_error_W',conservation_error,...
 'sealed_adiabatic_relative_error',adiabatic_error,'cross_language_scaled_errors',errors,...
 'local_models',[1 3 15],'canonical_valve_calibration_recovered',false,'passed',true);
if nargin>0
 fid=fopen(output_path,'w');assert(fid>=0);cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(report));clear cleanup;
end
fprintf('Pneumatic SI mass/energy, sonic flow, gravity and three cross-language cases passed.\n');
end
