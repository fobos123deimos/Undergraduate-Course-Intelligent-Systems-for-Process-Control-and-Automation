function result=run_wind_control(scheduled,duration,dt,points)
%RUN_WIND_CONTROL Sample-and-hold torque/pitch with wind steps at 20 and 40 s.
if nargin<1,scheduled=true;end
if nargin<2,duration=60;end
if nargin<3,dt=.02;end
if nargin<4,points=wind_control('design');end
assert(dt>0&&duration>0&&abs(duration/dt-round(duration/dt))<1e-9);
t=(0:dt:duration)';v=12+2*(t>=20)+2*(t>=40);n=numel(t);x=zeros(n,8);u=zeros(n,2);
p=wind_control('equilibrium',v(1));x(1,:)=p.state';previous=p.command;
for k=1:n-1
 command=wind_control('command',x(k,:)',v(k),points,previous,dt,scheduled);u(k,:)=command';
 f=@(z)wind_control('rhs',z,command,v(k));z=x(k,:)';
 a=f(z);b=f(z+dt*a/2);c=f(z+dt*b/2);d=f(z+dt*c);
 x(k+1,:)=(z+dt*(a+2*b+2*c+d)/6)';previous=command;
end
u(end,:)=u(end-1,:);assert(all(isfinite(x(:))));
result=struct('time',t,'wind',v,'state',x,'command',u,'scheduled',scheduled,...
 'speed_rmse',sqrt(mean((x(:,6)-1.2).^2)),'speed_peak_error',max(abs(x(:,6)-1.2)),...
 'pitch_peak_deg',max(x(:,8))*180/pi);
end
