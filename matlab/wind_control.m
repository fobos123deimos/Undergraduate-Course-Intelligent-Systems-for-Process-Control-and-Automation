function result=wind_control(action,varargin)
%WIND_CONTROL Later-map wind equilibrium, scaled LQR and PDC design exercise.
% Regulation state: [tower;blade;torsion;v_tower;v_blade;w_rotor;w_generator;pitch].
% Common absolute rotation is removed; commands are [torque;pitch_d].
switch action
 case 'rhs',result=rhs(varargin{:});
 case 'equilibrium',result=equilibrium(varargin{:});
 case 'linearize',result=linearize(varargin{:});
 case 'design',result=design();
 case 'weights',result=weights(varargin{:});
 case 'command',result=command(varargin{:});
 case 'variant',result=variant(varargin{:});
 otherwise,error('Unknown wind-control operation.');
end
end

function f=variant(x,u,v,name,frequency,damping)
if nargin<5,frequency=10;end
if nargin<6,damping=1;end
x=x(:);
if strcmp(name,'rigid_structure')&&numel(x)==4
 z=[0;0;x(1);0;0;x(2:4)];g=rhs(z,u,v);f=g([3 6 7 8]);
elseif strcmp(name,'second_order_pitch')&&numel(x)==9
 assert(frequency>0&&damping>0);g=rhs(x(1:8),u,v);g(8)=x(9);
 f=[g;frequency^2*(u(2)-x(8))-2*damping*frequency*x(9)];
else,error('Unknown variant or incompatible dimension.');end
end

function f=rhs(x,u,v)
x=x(:);u=u(:);assert(numel(x)==8&&numel(u)==2);
full=[x(1:2);x(3);0;x(4:7);x(8)];
d=paper_models('wind',full,[v;u]);
f=[x(4:5);x(6)-x(7);d(5:9)];
end

function point=equilibrium(v)
assert(isfinite(v)&&v>=12&&v<=16,'Study wind range is [12,16] m/s.');
torque=5e6/1.2;lo=0;hi=30*pi/180;
x=[0;0;torque/867637000;0;0;1.2;1.2;lo];
f=rhs(x,[torque;lo],v);assert(f(6)>0);
x(8)=hi;f=rhs(x,[torque;hi],v);assert(f(6)<0);
for k=1:50
 mid=(lo+hi)/2;x(8)=mid;f=rhs(x,[torque;mid],v);
 if f(6)>0,lo=mid;else,hi=mid;end
end
pitch=(lo+hi)/2;x(8)=pitch;f=rhs(x,[torque;pitch],v);
thrust=(436865+3*4435)*f(4)+3*4435*f(5);
x(1)=thrust/1981900;x(2)=thrust/120000;
point=struct('wind',v,'state',x,'command',[torque;pitch]);
end

function system=linearize(x,u,v)
sx=[1;5;.01;.2;1;.1;.1;.1];su=[1e6;.1];A=zeros(8);B=zeros(8,2);
for j=1:8
 delta=zeros(8,1);delta(j)=sx(j)*1e-5;
 A(:,j)=(rhs(x+delta,u,v)-rhs(x-delta,u,v))/(2*delta(j));
end
for j=1:2
 delta=zeros(2,1);delta(j)=su(j)*1e-5;
 B(:,j)=(rhs(x,u+delta,v)-rhs(x,u-delta,v))/(2*delta(j));
end
system=struct('A',A,'B',B,'state_scale',sx,'input_scale',su);
end

function points=design()
grid=[12 14 16];Q=diag([1 1 .2 1 1 100 100 1]);R=diag([2 1]);
points=struct([]);
for k=1:3
 p=equilibrium(grid(k));s=linearize(p.state,p.command,p.wind);
 S=diag(s.state_scale);U=diag(s.input_scale);A=S\s.A*S;B=S\s.B*U;
 % Stable invariant subspace solves CARE without the Control System Toolbox.
 H=[A -B*(R\B');-Q -A'];[V,L]=eig(H);idx=find(real(diag(L))<0);
 assert(numel(idx)==8,'Hamiltonian has no separated stable subspace.');
 basis=V(:,idx);P=real(basis(9:16,:)/basis(1:8,:));P=(P+P')/2;
 residual=A'*P+P*A-P*B*(R\B')*P+Q;
 gain=U*(R\(B'*P))/S;
 poles=eig(s.A-s.B*gain);err=norm(residual,Inf);
 assert(min(eig(P))>-1e-7&&err<1e-5&&max(real(poles))<0);
 p.gain=gain;p.A=s.A;p.B=s.B;p.care_residual=err;p.max_pole_real=max(real(poles));
 points(k)=p;
end
end

function h=weights(v,points)
grid=[points.wind];assert(isfinite(v)&&all(diff(grid)>0)&&v>=grid(1)&&v<=grid(end),'Outside scheduling grid.');
j=find(grid<=v,1,'last');j=min(j,numel(grid)-1);alpha=(v-grid(j))/(grid(j+1)-grid(j));
h=zeros(1,numel(grid));h(j:j+1)=[1-alpha alpha];
end

function u=command(x,v,points,previous,dt,scheduled)
if nargin<6,scheduled=true;end
assert(dt>0);h=weights(v,points);raw=zeros(2,1);
if scheduled
 for j=1:numel(points),raw=raw+h(j)*(points(j).command-points(j).gain*(x-points(j).state));end
else
 xe=zeros(8,1);ue=zeros(2,1);
 for j=1:numel(points),xe=xe+h(j)*points(j).state;ue=ue+h(j)*points(j).command;end
 raw=ue-points(ceil(numel(points)/2)).gain*(x-xe);
end
rate=[5e5;8*pi/180];lo=[0;0];hi=[6e6;30*pi/180];
u=min(hi,max(lo,previous+min(rate*dt,max(-rate*dt,raw-previous))));
end
