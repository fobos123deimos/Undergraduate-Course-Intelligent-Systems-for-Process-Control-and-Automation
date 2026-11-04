function u = mpc_control(A,B,x,reference,H,Nc,rho,previous)
%MPC_CONTROL Box-constrained quadratic MPC, piecewise constant final move.
% Inputs have bounds [0,1]; rho weights changes, not absolute input.
nx=numel(x);nu=size(B,2);F=zeros(H*nx,nx);G=zeros(H*nx,Nc*nu);
for i=1:H
 rows=(i-1)*nx+(1:nx);F(rows,:)=A^i;
 for j=1:i
  col=min(j,Nc);cols=(col-1)*nu+(1:nu);
  G(rows,cols)=G(rows,cols)+A^(i-j)*B;
 end
end
E=eye(Nc*nu);
for j=2:Nc,E((j-1)*nu+(1:nu),(j-2)*nu+(1:nu))=-eye(nu);end
anchor=[previous(:);zeros((Nc-1)*nu,1)];
Q=G'*G+rho*E'*E;c=G'*(F*x(:)-repmat(reference(:),H,1))-rho*E'*anchor;
z=repmat(previous(:),Nc,1);L=norm(Q,2);
for k=1:1200
 next=min(1,max(0,z-(Q*z+c)/L));residual=norm(next-z,Inf);z=next;
 if residual<1e-8,break;end
end
u=z(1:nu);
end
