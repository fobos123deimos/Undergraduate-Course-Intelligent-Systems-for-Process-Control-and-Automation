function dx = paper_models(name, x, u, options)
%PAPER_MODELS Kroll and Schulte (2014), doi:10.1016/j.asoc.2014.08.034.
% See benchmarks/README.md for state order, units and source qualifications.
% SISO/MIMO return next samples; other supported names return derivatives.
% No proprietary toolboxes required. Unknown industrial models are not replaced.
if nargin<4,options=struct;end
x=x(:);u=u(:);
switch lower(name)
 case 'siso'
  assert(numel(x)==2 && numel(u)==1);
  dx=x(1)*x(2)*(x(1)+2.5)/(1+x(1)^2*x(2)^2)+u;
 case 'mimo'
  assert(numel(x)==2 && numel(u)==2);
  dx=[x(1);x(1)*x(2)]/(1+x(2)^2)+u;
 case 'pendulum'
  m=.356;M=4.8;l=.56;g=9.81;mu=.035;a=1/(m+M);
  theta=x(1);omega=x(2);v=x(4);force=min(120,max(-120,u));friction=4.9*sign(v);
  s=sin(theta);c=cos(theta);
  ddtheta=(g*s-m*l*a*omega^2*c*s-a*c*(force-friction)-mu*omega/(m*l))/(2*l-m*l*a*c*c);
  ddx=2*a/(2-m*a*c*c)*(m*l*omega^2*s-.5*m*g*c*s+force-friction+c*mu*omega/(2*l));
  dx=[omega;ddtheta;v;ddx];
 case 'pneumatic'
  % Inputs are FIVE mass flows, not valve voltages (valves absent in paper).
  assert(numel(x)==4 && numel(u)==5 && abs(x(1))<=.125 && min(x(3:4))>0);
  area=2.8e-3;V=5e-4;kap=getopt(options,'kappa',1.4);
  R=getopt(options,'gas_constant',8.314);T=getopt(options,'temperature',293.15);
  mass=getopt(options,'load_mass',3); assert(mass>0);
  dx=[x(2);(area*(x(3)-x(4))-135*x(2)-21*sign(x(2)))/(mass+2.9);...
   kap*(R*T*(u(2)-u(1)-u(5))-area*x(3)*x(2))/(V+area*x(1));...
   kap*(-R*T*(u(4)-u(3)-u(5))+area*x(4)*x(2))/(V-area*x(1))];
 case 'hydrostatic'
  % Literal mixed-unit transcription: NOT a validated SI simulator.
  if ~isfield(options,'pump_speed'),error('Supply options.pump_speed explicitly.');end
  wp=options.pump_speed;load=getopt(options,'wheel_load',0);
  dx=[(-x(1)+241.67*u(1))/.13;(-x(2)+283.33*u(2))/.22;...
   10/1840.8*(145*x(1)*wp-170*x(2)*x(4)-.14*x(3));...
   ((-6.12)^2*(-23.3)^2*.98*.697*145e-4*x(2)*x(3)-.33*(-23.3)^2*x(4)-load*(-6.12)*(-23.3))/16512];
 case 'three_tank'
  assert(numel(x)==3 && numel(u)==2 && all(x>=0 & x<=.62) && all(u>=0 & u<=1e-4));
  q=@(dh) .5e-4*.48*sign(dh)*sqrt(2*9.81*abs(dh));
  q13=q(x(1)-x(3));q32=q(x(3)-x(2));
  opening=getopt(options,'outlet_openings',[0;0;0]);opening=opening(:);
  assert(numel(opening)==3 && all(opening>=0 & opening<=1));
  drain=opening*.5e-4*.56.*sqrt(2*9.81*x);
  dx=([-q13+u(1);q32+u(2);q13-q32]-drain)/.0154;
 case 'bioreactor'
  gamma=getopt(options,'gamma',.4);beta=getopt(options,'beta',.02);
  assert(all(x>=0 & x<=1) && u>=0 && gamma>0 && beta>0);
  growth=x(1)*(1-x(2))*exp(x(2)/gamma);
  dx=[-x(1)*u+growth;-x(2)*u+growth*(1+beta)/(1+beta-x(2))];
 case 'bioreactor_sample'
  dx=x;
  for k=1:50,dx=dx+.01*paper_models('bioreactor',dx,u,options);end
 case 'cstr'
  % Temperatures Celsius, time h, cooling input MJ/h (converted to kJ/h).
  assert(numel(x)==4 && numel(u)==2 && min(x(1:2))>=0 && min(x(3:4))>-273.15);
  assert(u(1)>=5 && u(1)<=35 && u(2)>=-8.5 && u(2)<=0);
  ca=x(1);cb=x(2);T=x(3);Tc=x(4);feed=getopt(options,'feed_concentration',5100);
  gamma=getopt(options,'gamma',.1);
  k1=1.287e12*exp(-9758.3/(T+273.15));k2=9.043e6*exp(-8560/(T+273.15));
  heat=-3.556e-4*(k1*(ca*4.2+cb*(-11))+k2*ca^2*(-41.85));
  dx=[-k1*ca-k2*ca^2+(feed-ca)*u(1);k1*(ca-cb)-cb*u(1);...
   heat+30.8285*(Tc-T)+(104.9-T)*u(1);86.688*(T-Tc)+gamma*u(2)*1000];
 case {'column_a','column_a_lv'}
  assert(numel(x)==82 && all(x(1:41)>=0 & x(1:41)<=1) && all(x(42:end)>0));
  if isempty(u),u=[2.70629;3.20629;.5;.5;1;.5;1];end
  if strcmpi(name,'column_a_lv')
   gain=getopt(options,'level_gain',10);
   if numel(u)==7,u=u([1 2 5 6 7]);end
   u=[u(1:2);max(0,.5+gain*(x(82)-.5));max(0,.5+gain*(x(42)-.5));u(3:5)];
  end
  L=u(1);V=u(2);D=u(3);B=u(4);F=u(5);zf=u(6);qf=u(7);
  c=x(1:41);m=x(42:82);vapor=1.5*c(1:40)./(1+.5*c(1:40));
  v=V*ones(40,1);v(21:40)=v(21:40)+(1-qf)*F;
  liquid=zeros(41,1);liquid(2:21)=3.70629+(m(2:21)-.5)/.063;
  liquid(22:40)=2.70629+(m(22:40)-.5)/.063;liquid(41)=L;
  dm=zeros(41,1);dmc=dm;
  for i=2:40
   dm(i)=liquid(i+1)-liquid(i)+v(i-1)-v(i);
   dmc(i)=liquid(i+1)*c(i+1)-liquid(i)*c(i)+v(i-1)*vapor(i-1)-v(i)*vapor(i);
  end
  dm(21)=dm(21)+F;dmc(21)=dmc(21)+F*zf;
  dm(1)=liquid(2)-v(1)-B;dmc(1)=liquid(2)*c(2)-v(1)*vapor(1)-B*c(1);
  dm(41)=v(40)-L-D;dmc(41)=v(40)*vapor(40)-(L+D)*c(41);
  dx=[(dmc-c.*dm)./m;dm];
 case 'wind'
  % Later ROSCO rotor-map variant, not exact reproduction of 2014 curves.
  assert(numel(x)==9 && numel(u)==3);
  mt=436865;mb=4435;n=3;M=diag([mt+n*mb n*mb 38759227 5025347]);M(1,2)=n*mb;M(2,1)=n*mb;
  D=diag([7e4 n*2e4 6215000 6215000]);D(3,4)=-6215000;D(4,3)=-6215000;
  K=diag([1981900 n*40000 867637000 867637000]);K(3,4)=-867637000;K(4,3)=-867637000;
  q=x(1:4);vel=x(5:8);veff=u(1)-vel(1)-vel(2);assert(veff>0);
  path=getopt(options,'rotor_map',fullfile(fileparts(mfilename('fullpath')),'..','benchmarks','data','Cp_Ct_Cq.NREL5MW.txt'));
  [ct,cq]=rotor_coefficients(path,vel(3)*63/veff,x(9));
  ft=.5*1.225*pi*63^2*ct*veff^2;tr=.5*1.225*pi*63^3*cq*veff^2;
  dx=[vel;M\([ft;ft;tr;-u(2)]-D*vel-K*q);(u(3)-x(9))/.1];
 case {'tennessee_eastman','alstom_gasifier','throttle','data_repositories'}
  error('This industrial case requires its documented external simulator or measured dataset; see benchmarks/README.md.');
 otherwise,error('Unknown benchmark name: %s',name);
end
assert(all(isfinite(dx)),'Model produced nonfinite values.');
end

function v=getopt(s,name,fallback)
if isfield(s,name),v=s.(name);else,v=fallback;end
end
function [ct,cq]=rotor_coefficients(path,tsr,beta)
persistent cachedpath pitch ratio Ct Cq
if isempty(cachedpath) || ~strcmp(cachedpath,path)
 fid=fopen(path,'r');if fid<0,error('Rotor-map file not found.');end
 rows={};line=fgetl(fid);
 while ischar(line)
  line=strtrim(line);
  if ~isempty(line) && line(1)~='#',rows{end+1}=sscanf(line,'%f')';end
  line=fgetl(fid);
 end
 fclose(fid);pitch=rows{1};ratio=rows{2};n=numel(ratio);
 Ct=vertcat(rows{4+n:3+2*n});Cq=vertcat(rows{4+2*n:3+3*n});cachedpath=path;
end
p=beta*180/pi;
if p<pitch(1) || p>pitch(end) || tsr<ratio(1) || tsr>ratio(end),error('Rotor-map extrapolation is forbidden.');end
ct=interp2(pitch,ratio,Ct,p,tsr,'linear');cq=interp2(pitch,ratio,Cq,p,tsr,'linear');
end
