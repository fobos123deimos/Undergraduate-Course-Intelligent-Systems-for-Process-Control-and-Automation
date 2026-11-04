function varargout=pneumatic_physical(action,varargin)
%PNEUMATIC_PHYSICAL Separate SI mass/energy variant; not a recovered valve fit.
% State [position;velocity;massI;massII;temperatureI;temperatureII].
% Source and assumption audit: benchmarks/PNEUMATIC_AUDIT.md.
switch lower(action)
 case 'parameters',varargout{1}=parameters();
 case 'orifice',varargout{1}=orifice(varargin{:});
 case 'observe',[varargout{1:nargout}]=observe(varargin{:});
 case 'state',varargout{1}=from_pressures(varargin{:});
 case 'equilibrium',varargout{1}=equilibrium(varargin{:});
 case {'rhs','balances'}
  validate_parameters(varargin{3});[varargout{1:nargout}]=balances(varargin{:});
 case 'local',varargout{1}=local_model(varargin{1});
 case 'simulate'
  input=varargin{1};initial=varargin{2};p=varargin{3};duration=varargin{4};samples=varargin{5};
  assert(duration>0&&samples>=2);validate_parameters(p);observe(initial,p);
  [t,x]=ode45(@(tt,xx)balances(xx,input(tt),p),linspace(0,duration,samples),initial,...
   odeset('RelTol',1e-9,'AbsTol',1e-11,'MaxStep',.005));
  varargout{1}=struct('time',t,'state',x);
 otherwise,error('pneumatic_physical:Action','Unknown action.');
end
end

function p=parameters()
p=struct('area',2.8e-3,'half_stroke',.125,'midpoint_volume',5e-4,...
 'piston_mass',2.9,'load_mass',3,'viscous',135,'coulomb',21,'valve_gain',1e-4,...
 'voltage_limit',10,'supply_pressure',9e5,'exhaust_pressure',1e5,...
 'reservoir_temperature',293.15,'universal_R',8.31446261815324,...
 'air_molar_mass',.0289644,'gamma',1.4,'gravity',9.81,...
 'port_width',.002,'discharge_coefficient',.7,'bypass_area',0,...
 'friction_velocity',.005,'wall_conductance',0,'wall_temperature',293.15);
end

function validate_parameters(p)
names=fieldnames(parameters());v=zeros(numel(names),1);
for j=1:numel(names)
 assert(isfield(p,names{j})&&isscalar(p.(names{j}))&&isreal(p.(names{j})),'Invalid parameter.');
 v(j)=p.(names{j});
end
assert(all(isfinite(v)),'Finite parameters required.');
positive={'area','half_stroke','midpoint_volume','piston_mass','valve_gain','voltage_limit',...
 'supply_pressure','exhaust_pressure','reservoir_temperature','universal_R','air_molar_mass',...
 'port_width','discharge_coefficient','friction_velocity','wall_temperature'};
for j=1:numel(positive),assert(p.(positive{j})>0,'Positive physical coefficient required.');end
nonnegative={'load_mass','viscous','coulomb','bypass_area','wall_conductance'};
for j=1:numel(nonnegative),assert(p.(nonnegative{j})>=0,'Nonnegative coefficient required.');end
assert(p.gamma>1&&p.discharge_coefficient<=1&&p.supply_pressure>p.exhaust_pressure);
assert(p.midpoint_volume>p.area*p.half_stroke,'Positive residual volumes required.');
end

function q=orifice(pa,pb,ta,tb,area,p)
assert(isreal([pa pb ta tb area])&&all(isfinite([pa pb ta tb area]))&&min([pa pb ta tb])>0&&area>=0);
if pa==pb||area==0,q=0;return;end
if pa>pb,sgn=1;up=pa;down=pb;temp=ta;else,sgn=-1;up=pb;down=pa;temp=tb;end
g=p.gamma;R=p.universal_R/p.air_molar_mass;r=down/up;critical=(2/(g+1))^(g/(g-1));
if r<=critical,phi=sqrt(g)*(2/(g+1))^((g+1)/(2*(g-1)));
else,phi=sqrt(2*g/(g-1)*(r^(2/g)-r^((g+1)/g)));end
q=sgn*p.discharge_coefficient*area*up/sqrt(R*temp)*phi;
end

function [pressure,volume]=observe(x,p)
x=x(:);
assert(isreal(x)&&numel(x)==6&&all(isfinite(x(:)))&&min(x(3:6))>0);
assert(abs(x(1))<=p.half_stroke+1e-12,'Position exceeds stroke; no impact model.');
volume=[p.midpoint_volume+p.area*x(1);p.midpoint_volume-p.area*x(1)];
pressure=x(3:4).*(p.universal_R/p.air_molar_mass).*x(5:6)./volume;
end

function x=from_pressures(position,velocity,pressure,temperature,p)
pressure=pressure(:);temperature=temperature(:);
assert(numel(pressure)==2&&numel(temperature)==2&&all(isfinite(pressure))&&min(pressure)>0);
volume=[p.midpoint_volume+p.area*position;p.midpoint_volume-p.area*position];
x=[position;velocity;pressure.*volume./((p.universal_R/p.air_molar_mass)*temperature);temperature];
observe(x,p);
end

function x=equilibrium(position,mean_pressure,p)
validate_parameters(p);assert(p.bypass_area==0,'Equilibrium requires zero bypass.');
delta=(p.piston_mass+p.load_mass)*p.gravity/p.area;
pressure=mean_pressure+[delta;-delta]/2;
assert(min(pressure)>p.exhaust_pressure&&max(pressure)<p.supply_pressure);
if p.wall_conductance>0,T=p.wall_temperature;else,T=p.reservoir_temperature;end
x=from_pressures(position,0,pressure,T*[1;1],p);
end

function [dx,info]=balances(x,voltage,p,external_force)
if nargin<4,external_force=0;end
assert(isreal(voltage)&&isreal(external_force)&&isfinite(voltage)&&isfinite(external_force));x=x(:);
[pressure,volume]=observe(x,p);R=p.universal_R/p.air_molar_mass;cv=R/(p.gamma-1);cp=p.gamma*cv;
u=max(-p.voltage_limit,min(p.voltage_limit,voltage));spool=p.valve_gain*u;opened=p.port_width*abs(spool);
node_p=[p.supply_pressure;p.exhaust_pressure;pressure];node_t=[p.reservoir_temperature;p.reservoir_temperature;x(5:6)];
areas=[opened*(u<0);opened*(u>0);opened*(u<0);opened*(u>0);p.bypass_area];
links=[3 2;1 3;1 4;4 2;3 4];flows=zeros(5,1);dm=zeros(2,1);enthalpy=zeros(2,1);
for j=1:5
 a=links(j,1);b=links(j,2);q=orifice(node_p(a),node_p(b),node_t(a),node_t(b),areas(j),p);flows(j)=q;
 if q>=0,Tup=node_t(a);else,Tup=node_t(b);end
 transported=q*cp*Tup;
 if a>=3,dm(a-2)=dm(a-2)-q;enthalpy(a-2)=enthalpy(a-2)-transported;end
 if b>=3,dm(b-2)=dm(b-2)+q;enthalpy(b-2)=enthalpy(b-2)+transported;end
end
dvolume=[p.area*x(2);-p.area*x(2)];heat=p.wall_conductance*(p.wall_temperature-x(5:6));
denergy=enthalpy+heat-pressure.*dvolume;dtemperature=(denergy-cv*x(5:6).*dm)./(cv*x(3:4));
friction=p.viscous*x(2)+p.coulomb*tanh(x(2)/p.friction_velocity);mass=p.piston_mass+p.load_mass;
acceleration=(p.area*(pressure(1)-pressure(2))-friction-mass*p.gravity-external_force)/mass;
dx=[x(2);acceleration;dm;dtemperature];
dp=R./volume.*(x(5:6).*dm+x(3:4).*dtemperature)-pressure.*dvolume./volume;
info=struct('pressures',pressure,'volumes',volume,'mass_flows',flows,'mass_rate',dm,...
 'enthalpy_rate',enthalpy,'heat_rate',heat,'internal_energy_rate',denergy,...
 'pressure_rate',dp,'friction',friction,'voltage',u,'spool_m',spool,'orifice_area_m2',opened);
end

function result=local_model(index)
switch index
 case 1,mass=0;position=0;c=[-26 -8.7e6 1.1e10];
 case 3,mass=6;position=0;c=[-11 -8.9e6 1e10];
 case 15,mass=6;position=.08;c=[-14 -1.06e7 1.24e10];
 otherwise,error('Only published local models1,3,15 are available.');
end
M=mass+2.9;A=[0 1 0;0 -135/M 2.8e-3/M;0 c(2) c(1)];B=[0;0;c(3)*1e-4];
result=struct('index',index,'load_kg',mass,'position_m',position,'A',A,'B',B,'C',[1 0 0],...
 'pressure_coefficients',c);
end
