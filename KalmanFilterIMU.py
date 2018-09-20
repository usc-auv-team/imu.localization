import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['figure.figsize'] = (10, 8)

# intial parameters
n_iter = 200
sigma = 0.05
sz = (n_iter,) # size of array
x = 0.5 # truth value (typo in example at top of p. 13 calls this z)
z = np.zeros(n_iter)
z[:50] = np.random.normal(x,sigma,size=50) # observations (normal about x, sigma=0.1)
z[50:100] = np.random.normal(0,sigma,size=50)
z[100:150] = np.random.normal(x,sigma,size=50)
z[150:200] = np.random.normal(0,sigma,size=50)
testNewTruth = False
confirmNewTruth = False
indexVal = 0
totalVelocity = 0.0
totalVelocityMeasured = 0.0

Q = 1e-5 # process variance

# allocate space for arrays
xhat=np.zeros(sz)      # a posteri estimate of x
P=np.zeros(sz)         # a posteri error estimate
xhatminus=np.zeros(sz) # a priori estimate of x
Pminus=np.zeros(sz)    # a priori error estimate
G=np.zeros(sz)         # gain or blending factor

R = sigma**2 # estimate of measurement variance, change to see effect

# intial guesses
xhat[0] = 0.0
P[0] = 1.0

for k in range(1,n_iter):

    if (confirmNewTruth and abs(z[k]-z[k-1])<3*sigma):
        confirmNewTruth = False
        xhatminus[k] = 0.0
        Pminus[k] = 1.0+Q
        indexVal = 0
    else:
        # time update
        xhatminus[k] = xhat[k-1]
        Pminus[k] = P[k-1]+Q

    if (testNewTruth):
        if (abs(z[k]-z[k-1])<3*sigma):
            confirmNewTruth = True
            testNewTruth = False

    # measurement update
    G[k] = Pminus[k]/( Pminus[k]+R)
    xhat[k] = xhatminus[k]+G[k]*(z[k]-xhatminus[k])
    P[k] = (1-G[k])*Pminus[k]

    #Velocity calculation
    totalVelocity += 1/2*(xhat[k]+xhat[k-1])*1.0
    totalVelocityMeasured += 1/2*(z[k]+z[k-1])*1.0

    # checking for different truth
    if (abs(z[k]-xhat[k])>3*sigma and indexVal>3):
        testNewTruth = True

    indexVal+=1

print("Total Velocity" + str(totalVelocity))
print("Total Velocity Measured" + str(totalVelocityMeasured))


plt.figure()
plt.plot(z,'k+',label='noisy measurements')
plt.plot(xhat,'b-',label='a posteri estimate')
plt.axhline(x,color='g',label='truth value 1')
plt.axhline(0,color='g',label='truth value 2')
plt.axvline(50,color='g')
plt.axvline(100,color='g')
plt.axvline(150,color='g')
plt.legend()
plt.title('Estimate vs. iteration step', fontweight='bold')
plt.xlabel('Iteration')
plt.ylabel('Voltage')

#plt.figure()
#valid_iter = range(1,n_iter) # Pminus not valid at step 0
#plt.plot(valid_iter,Pminus[valid_iter],label='a priori error estimate')
#plt.title('Estimated $\it{\mathbf{a \ priori}}$ error vs. iteration step', fontweight='bold')
#plt.xlabel('Iteration')
#plt.ylabel('$(Voltage)^2$')
#plt.setp(plt.gca(),'ylim',[0,.01])
plt.show()
