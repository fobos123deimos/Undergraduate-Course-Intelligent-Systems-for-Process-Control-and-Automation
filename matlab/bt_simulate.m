function trace = bt_simulate(t,x0,U,p)
%BT_SIMULATE Nonlinear simulation of a declared piecewise-constant schedule.
% U is one five-element held vector or (numel(t)-1)-by-5 interval rows.
% An analytic volume forecast rejects any schedule reaching min_volume;
% there is no extrapolation through an empty tank and no state clipping.
if nargin<4,p=bt_parameters();end
if ~isnumeric(t)||~isreal(t)||~isvector(t)||numel(t)<2||any(~isfinite(t(:)))||any(diff(t(:))<=0)
 error('bt:time','Supply at least two finite, strictly increasing times.');
end
t=t(:);N=numel(t);
if isnumeric(U)&&isvector(U)&&numel(U)==5,U=repmat(U(:)',N-1,1);end
if ~isnumeric(U)||~isreal(U)||~isequal(size(U),[N-1,5])
 error('bt:schedule','Use a held five-vector or one five-input row per time interval.');
end
[x0,~,p]=bt_validate(x0,U(1,:),p);
for k=1:N-1,bt_validate(x0,U(k,:),p);end
volume=x0(2)+[0;cumsum(diff(t).*(U(:,1)+U(:,2)-U(:,5))/p.rho)];
if any(volume<=p.min_volume)
 error('bt:emptyTank','The requested schedule reaches the minimum volume; shorten the horizon or change the flow.');
end
x=zeros(N,2);x(1,:)=x0';first=1;
while first<N
 last=first;
 while last<N-1&&isequal(U(last+1,:),U(first,:)),last=last+1;end
 input=U(first,:)';grid=t(first:last+1);
 minV=min(volume(first:last+1));inlet=input(1)+input(2);
 maxStep=min(diff(grid))/2;
 if inlet>0,maxStep=min(maxStep,.1*p.rho*minV/inlet);end
 options=odeset('RelTol',1e-10,'AbsTol',[1e-12,1e-12],'MaxStep',maxStep);
 [~,values]=ode45(@(time,state)bt_rhs(time,state,input,p),grid,x(first,:)',options);
 if numel(grid)==2,x(last+1,:)=values(end,:);
 else,x(first:last+1,:)=values;end
 first=last+1;
end
trace=struct('t',t,'x',x,'u',[U;U(end,:)],'interval_inputs',U,...
 'mass',p.rho*x(:,2),'solute_mass',p.rho*x(:,2).*x(:,1),...
 'volume_forecast',volume,'rho',p.rho,'min_volume',p.min_volume);
end
