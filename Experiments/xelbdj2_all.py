def celbdj(nc0: np.float8, mc0: np.float8) -> np.float8:
	"""
	Simultaneous computation of associate complete elliptic integrals of third kind, B(m), D(m), and J(n|m)

	Parameters
	----------
	nc0 : float
		Argument of the complete elliptic integral of third kind
	mc0 : float
		Argument of the complete elliptic integral of third kind

	Returns
	-------
	celb : float
		Value of the complete elliptic integral of third kind
	celd : float
		Value of the complete elliptic integral of third kind
	celj : float
		Value of the complete elliptic integral of third kind

	Notes
	-----
	Reference: Fukushima, T, (2013) J. Comp. Appl. Math., 253, 142-157
		Fast computation of a general complete elliptic integral
		of third kind by half and double argument transformations

	Restricted Version with Assumptions: 0 < mc, 0 < nc

	Author: Fukushima, T. <
"""
	logical flag
	integer IMAX,i,is,ie,err
	IMAX=40
	real*8 y(0:IMAX),x(0:IMAX),c(0:IMAX),d(0:IMAX),a(0:IMAX)
	real*8 mc,nc,m,n,yj,celk,yi,ye,dj,m1,kc0,temp
	real*8 PIHALF,EPS,THIRD
	PIHALF=1.5707963267948966
	EPS=1.11e-16
	THIRD=1./3.
	
	real*8 B(IMAX)
	first = True
	save B,first
	if mc0<0:
		print("(celbdj) Out of domain: mc <= 0")
		return None
	if nc0<0:
		print("(celbdj) Out of domain: nc <= 0")
		return
	endif
	if(mc0<1.):
		mc=mc0;nc=nc0
	elif(mc0>1.0):
        mc=1./mc0
        nc=nc0*mc
    else:
		celb=PIHALF*0.5
		celd=PIHALF*0.5
		celj=PIHALF/(nc0+np.sqrt(nc0))
		return celb,celd,celj
	if first:
		first= False
		for i in range(0,IMAX):
			B[i]=1.0/dble(2*i+1)
	celb, celd = celbd(mc)
	if(nc==mc)
		celj=celb/mc
		goto 4  
	m=1.d0-mc; n=1.d0-nc
	flag=nc.lt.mc.or.(n*nc).gt.(nc-mc)
	if(flag) then
		y(0)=(nc-mc)/(nc*m)
	else
		y(0)=n/m
	endif
	is=0
	if(y(0).gt.0.5d0) then
		x(0)=1.d0-y(0)
		do i=0,IMAX
			c(i)=sqrt(x(i))
			d(i)=sqrt(mc+m*x(i))
			x(i+1)=(c(i)+d(i))/(1.d0+d(i))
			if(x(i+1).gt.0.5d0) then
				y(i+1)=y(i)/((1.d0+c(i))*(1.d0+d(i)))
				is=i+1
				goto 1
			endif
			y(i+1)=1.d0-x(i+1)
		enddo
		write(*,"(a30,i5)") "(celbdj) No Conv. x-Transf. i=",i
		return
	endif
	1 continue
	do i=is,IMAX
		c(i)=sqrt(1.d0-y(i))
		d(i)=sqrt(1.d0-m*y(i))
		y(i+1)=y(i)/((1.d0+c(i))*(1.d0+d(i)))
		if(abs(y(i+1)).lt.0.325d0) goto 2
	enddo
	write(*,"(a30,i5)") "(celbdj) No Conv. y-Transf. i=",i
	return
	2 continue
	ie=i+1
	ye=y(ie)
	celk=celb+celd
	a(0)=celd
	celj=a(0)
	yi=ye
	a(1)=((1.d0+2.d0*m)*celd-celb)*THIRD
	dj=a(1)*yi
	i=1
	if(abs(dj).lt.EPS*abs(celj)) goto 3
	celj=celj+dj
	m1=1.d0+m
	do i=2,IMAX
		yi=yi*ye
		a(i)=(1.d0-B(i))*m1*a(i-1)-(1.d0-2.d0*B(i))*m*a(i-2)
		dj=a(i)*yi
		if(abs(dj).lt.EPS*abs(celj)) goto 3
		celj=celj+dj
	enddo
	write(*,"(a30,i5)") "(celbdj) No Conv. Series. i=",i
	return
	3 continue
	do i=ie-1,0,-1
		celj=(2.d0*(c(i)+d(i))*celj-y(i)*celk)/(c(i)*d(i)*(1.d0+c(i))*(1.d0+d(i)))
	enddo
	if(flag) then
		celj=(nc*celk-mc*celj)/(nc*nc)
	endif
	4 continue
	if(mc0.gt.1.d0) then
		kc0=sqrt(mc0)
		temp=celb
		celb=celd/kc0
		celd=temp/kc0
		celj=celj/(mc0*kc0)
	endif
	!write(*,"(a30,1p3e15.7)") "(celbdj) nc0,mc0,celj=",nc0,mc0,celj
	return celb,celd,celj