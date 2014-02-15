import unittest
from SimPEG import *
import simpegEM as EM
from scipy.constants import mu_0
from simpegEM.Utils.Ana import hzAnalyticDipoleT
import matplotlib.pyplot as plt


class TDEM_bTests(unittest.TestCase):

    def setUp(self):

        cs = 5.
        ncx = 20
        ncy = 6
        npad = 20
        hx = Utils.meshTensors(((0,cs), (ncx,cs), (npad,cs)))
        hy = Utils.meshTensors(((npad,cs), (ncy,cs), (npad,cs)))
        mesh = Mesh.Cyl1DMesh([hx,hy], -hy.sum()/2)
        model = Model.Vertical1DModel(mesh)

        opts = {'txLoc':0.,
                'txType':'VMD_MVP',
                'rxLoc':np.r_[150., 0.],
                'rxType':'bz',
                'timeCh':np.logspace(-4,-2,20),
                }
        self.dat = EM.TDEM.DataTDEM1D(**opts)

        self.prb = EM.TDEM.ProblemTDEM_b(mesh, model)
        self.prb.setTimes([1e-5, 5e-5, 2.5e-4], [150, 150, 150])
        self.sigma = np.ones(mesh.nCz)*1e-8
        self.sigma[mesh.vectorCCz<0] = 0.1
        self.prb.pair(self.dat)

    def test_analitic_b(self):
        bz_calc = self.dat.dpred(self.sigma)
        bz_ana = mu_0*hzAnalyticDipoleT(self.dat.rxLoc[0], self.prb.times, self.sigma[0])

        diff = np.linalg.norm(bz_calc.flatten() - bz_ana.flatten())/np.linalg.norm(bz_ana.flatten())
        self.assertTrue(diff<0.05)


class TDEM_bDerivTests(unittest.TestCase):

    def setUp(self):

       cs = 5.
       ncx = 20
       ncy = 6
       npad = 20
       hx = Utils.meshTensors(((0,cs), (ncx,cs), (npad,cs)))
       hy = Utils.meshTensors(((npad,cs), (ncy,cs), (npad,cs)))
       mesh = Mesh.Cyl1DMesh([hx,hy], -hy.sum()/2)
       model = Model.Vertical1DModel(mesh)

       opts = {'txLoc':0.,
               'txType':'VMD_MVP',
               'rxLoc':np.r_[150., 0.],
               'rxType':'bz',
               'timeCh':np.logspace(-4,-2,20),
               }
       self.dat = EM.TDEM.DataTDEM1D(**opts)

       self.prb = EM.TDEM.ProblemTDEM_b(mesh, model)
       self.prb.setTimes([1e-5, 5e-5, 2.5e-4], [10, 10, 10])
       self.sigma = np.ones(mesh.nCz)*1e-8
       self.sigma[mesh.vectorCCz<0] = 0.1
       self.prb.pair(self.dat)
       self.mesh = mesh


    def test_AhVec(self):
        """
            Test that fields and AhVec produce consistent results
        """

        prb = self.prb

        sigma = np.ones(self.prb.mesh.nCz)*1e-8
        sigma[prb.mesh.vectorCCz<0] = 0.1
        u = prb.fields(sigma)
        Ahu = prb.AhVec(sigma, u)
        
        V1 = Ahu.get_b(0)
        V2 = 1/prb.getDt(0)*prb.MfMui*u.get_b(-1)
        self.assertTrue(np.linalg.norm(V1-V2)/np.linalg.norm(V2) < 1.e-6)
        
        V1 = Ahu.get_e(0)
        self.assertTrue(np.linalg.norm(V1) < 1.e-6)

        for i in range(1,u.nTimes):
            
            dt = prb.getDt(i)
            
            V1 = Ahu.get_b(i)
            V2 = 1/dt*prb.MfMui*u.get_b(i-1)
            self.assertTrue(np.linalg.norm(V1)/np.linalg.norm(V2) < 1.e-6)

            V1 = Ahu.get_e(i)
            V2 = prb.MeSigma*u.get_e(i)
            self.assertTrue(np.linalg.norm(V1)/np.linalg.norm(V2) < 1.e-6)

    def test_AhVecVSMat_OneTS(self):

        prb = self.prb
        prb.setTimes([1e-5], [1])

        sigma = np.ones(prb.mesh.nCz)*1e-8
        sigma[prb.mesh.vectorCCz<0] = 0.1
        prb.makeMassMatrices(sigma)

        dt = prb.getDt(0)
        a11 = 1/dt*prb.MfMui*sp.eye(prb.mesh.nF)
        a12 = prb.MfMui*prb.mesh.edgeCurl
        a21 = prb.mesh.edgeCurl.T*prb.MfMui
        a22 = -prb.MeSigma
        A = sp.bmat([[a11,a12],[a21,a22]])

        f = prb.fields(sigma)
        u1 = A*f.fieldVec()
        u2 = prb.AhVec(sigma,f).fieldVec()

        self.assertTrue(np.linalg.norm(u1-u2)/np.linalg.norm(u1)<1e-12)

    def test_solveAhVSMat_OneTS(self):
        prb = self.prb

        prb.setTimes([1e-5], [1])

        sigma = np.ones(prb.mesh.nCz)*1e-8
        sigma[prb.mesh.vectorCCz<0] = 0.1
        prb.makeMassMatrices(sigma)

        dt = prb.getDt(0)
        a11 = 1/dt*prb.MfMui*sp.eye(prb.mesh.nF)
        a12 = prb.MfMui*prb.mesh.edgeCurl
        a21 = prb.mesh.edgeCurl.T*prb.MfMui
        a22 = -prb.MeSigma
        A = sp.bmat([[a11,a12],[a21,a22]])

        f = prb.fields(sigma)
        f.set_b(np.zeros((prb.mesh.nF,1)),0)
        f.set_e(np.random.rand(prb.mesh.nE,1),0)

        u1 = prb.solveAh(sigma,f).fieldVec().flatten()
        u2 = sp.linalg.spsolve(A.tocsr(),f.fieldVec())

        self.assertTrue(np.linalg.norm(u1-u2)<1e-8)

    def test_solveAhVsAhVec(self):

        prb = self.prb
        mesh = self.prb.mesh

        sigma = np.ones(self.prb.mesh.nCz)*1e-8
        sigma[self.prb.mesh.vectorCCz<0] = 0.1
        self.prb.makeMassMatrices(sigma)

        f = EM.TDEM.FieldsTDEM(prb.mesh, 1, prb.times.size, 'b')
        for i in range(f.nTimes):
            f.set_b(np.zeros((mesh.nF, 1)), i)
            f.set_e(np.random.rand(mesh.nE, 1), i)

        Ahf = prb.AhVec(sigma, f)
        f_test = prb.solveAh(sigma, Ahf)

        u1 = f.fieldVec()
        u2 = f_test.fieldVec()
        self.assertTrue(np.linalg.norm(u1-u2)<1e-8)

    def test_DerivG(self):
        """
            Test the derivative of c with respect to sigma
        """

        # Random model and perturbation
        sigma = np.random.rand(self.prb.mesh.nCz)
        f = self.prb.fields(sigma)
        dm = np.random.rand(self.prb.mesh.nCz)
        h = 1.

        a = np.linalg.norm(self.prb.AhVec(sigma+h*dm, f).fieldVec() - self.prb.AhVec(sigma, f).fieldVec())
        b = np.linalg.norm(self.prb.AhVec(sigma+h*dm, f).fieldVec() - self.prb.AhVec(sigma, f).fieldVec() - h*self.prb.G(sigma, dm, u=f).fieldVec())
        # Assuming that the gradient is exact to machine precision
        self.assertTrue(b<1e-16)

    def test_Deriv_dUdM(self):

        prb = self.prb
        prb.setTimes([1e-5, 1e-4, 1e-3], [10, 10, 10])
        mesh = self.mesh
        sigma = self.sigma

        d_sig = sigma.copy() #np.random.rand(mesh.nCz)
        d_sig[d_sig==1e-8] = 0

        num = 10
        error = np.zeros(num)
        order = 0
        hv = np.logspace(-1.2,-3, num)
        print '\n'
        for i, h in enumerate(hv):
            f = prb.fields(sigma)
            fstep = prb.fields(sigma + h*d_sig)
            dcdm = prb.G(sigma, h*d_sig, u=f) # TODO: make negative!?!?
            dudm = prb.solveAh(sigma, dcdm)

            linear = np.linalg.norm(f.fieldVec() - fstep.fieldVec())
            quad = np.linalg.norm(f.fieldVec() - fstep.fieldVec() - dudm.fieldVec())
            error[i] = quad
            if i > 0:
                order = np.log(error[i]/error[i-1])/np.log(hv[i]/hv[i-1])

            # print np.log(linearB/quadB)/np.log(h)
            print h, linear, quad, order

        self.assertTrue(order > 1.8)

    def test_Deriv_J(self):

        prb = self.prb
        prb.setTimes([1e-5, 1e-4, 1e-3], [10, 10, 10])
        mesh = self.mesh
        sigma = self.sigma

        d_sig = 0.8*sigma #np.random.rand(mesh.nCz)
        d_sig[d_sig==1e-8] = 0


        derChk = lambda m: [prb.data.dpred(m), lambda mx: -prb.Jvec(sigma, mx)]
        print '\n'
        passed = Tests.checkDerivative(derChk, sigma, plotIt=False, dx=d_sig, num=2, eps=1e-20)
        self.assertTrue(passed)




if __name__ == '__main__':
    unittest.main()
