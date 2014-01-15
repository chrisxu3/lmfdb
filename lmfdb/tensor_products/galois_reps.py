r"""

AUTHORS: Chris Wuthrich, 2014

Example:

sage: import lmfdb
sage: from lmfdb.tensor_products.galois_reps import *
sage: V = GaloisRepresentation(EllipticCurve("37a1"))
sage: V.motivic_weight
1

sage: from lmfdb.WebCharacter import *
sage: chi = WebDirichletCharacter(modulus=37,number=4)
sage: V = GaloisRepresentation(chi)
sage: V.langlands
True

sage: from lmfdb.math_classes import ArtinRepresentation
sage: rho = ArtinRepresentation(2,23,1)
sage: V = GaloisRepresentation(rho)
sage: V.dim
2

"""

########################################################################
#       Copyright (C) Chris Wuthrich 2014
#
#  Distributed under the terms of the GNU General Public License (GPL)
#
#                  http://www.gnu.org/licenses/
########################################################################

#import os
#import weakref

import lmfdb.base
from lmfdb.WebCharacter import * #WebDirichletCharacter
from lmfdb.lfunctions.Lfunction_base import Lfunction

from sage.structure.sage_object import SageObject
#from sage.schemes.elliptic_curves.constructor import EllipticCurve
#from sage.rings.rational import Rational
from sage.rings.integer_ring import ZZ
from sage.rings.complex_field import ComplexField

class GaloisRepresentation( Lfunction):

    def __init__(self, thingy):
        """
        Class representing a L-function coming from a Galois representation.
        Typically, dirichlet characters, artin reps, elliptic curves,...
        can give rise to such a class.

        It can be used for tensor two such together (mul below) and a
        L-function class can be extracted from it.
        """

        # this is an important global variable.
        # it is the maximum of the imag parts of values s at
        # which we will compute L(s,.)
        self.max_imaginary_part = "40"

        if isinstance(thingy, sage.schemes.elliptic_curves.ell_rational_field.EllipticCurve_rational_field):
            self.init_elliptic_curve(thingy)

        if isinstance(thingy, lmfdb.WebCharacter.WebDirichletCharacter):
            self.init_dir_char(thingy)

        if isinstance(thingy, lmfdb.math_classes.ArtinRepresentation):
            self.init_artin_rep(thingy)

        if isinstance(thingy, lmfdb.modular_forms.elliptic_modular_forms.backend.web_modforms.WebNewForm):
            self.init_elliptic_modular_form(thingy)

        self.level = self.conductor
        self.degree = self.dim
        self.poles = []
        self.residues = []

## Various ways to construct such a class

    def init_elliptic_curve(self, E):
        """
        Returns the Galois rep of an elliptic curve over Q
        """
        # needed ?
        # Remove the ending number (if given) in the label to only get isogeny
        # class
        #while self.label[len(self.label) - 1].isdigit():
            #self.label = self.label[0:len(self.label) - 1]
        ## Create the elliptic curve in the database
        #Edata = LfunctionDatabase.getEllipticCurveData(self.label + '1')
        #if Edata is None:
            #raise KeyError('No elliptic curve with label %s exists in the database' % self.label)
        #self.db_object = Edata

        self.original_object = [E]
        self.object_type = "ellipticcurve"
        self.dim = 2
        self.weight = 2
        self.motivic_weight = 1
        self.conductor = E.conductor()
        self.sign = E.root_number()
        self.mu_fe = []
        self.nu_fe = [ZZ(1)/ZZ(2)]
        self.gammaV = [0, 1]
        self.langlands = True
        self.selfdual = True
        self.primitive = True
        self.set_dokchitser_Lfunction()
        self.set_number_of_coefficients()
        self.dirichlet_coefficients = E.anlist(self.numcoeff)[1:]
        self.coefficient_type = 2
        self.coefficient_period = 0
        self.ld.gp().quit()

    def init_dir_char(self, chi):
        """
        Initiate with a Web Dirichlet character.
        """
        self.original_object = [chi]
        chi = chi.chi.primitive_character()
        self.object_type = "dirichletcharacter"
        self.dim = 1
        self.weight = 0
        self.motivic_weight = 0
        self.conductor = chi.conductor()
        if chi.is_odd():
            aa = 1
            bb = I
        else:
            aa = 0
            bb = 1
        self.sign = chi.gauss_sum_numerical() / (bb * float(sqrt(chi.modulus())) )
        # this has now type python complex. later we need a gp complex
        self.sign = ComplexField()(self.sign)
        self.mu_fe = [aa]
        self.nu_fe = []
        self.gammaV = [aa]
        self.langlands = True
        self.selfdual = all(  abs(chi(m).imag) < 0.0001 for m in range(chi.modulus() ) )
        self.primitive = True
        self.set_dokchitser_Lfunction()
        self.set_number_of_coefficients()
        self.dirichlet_coefficients = [ chi(m) for m in range(self.numcoeff + 1) ]
        if self.selfdual:
            self.coefficient_type = 2
        else:
            self.coefficient_type = 3
        self.coefficient_period = chi.modulus()
        self.ld.gp().quit()


    def init_artin_rep(self, rho):
        """
        Initiate with an Artin representation
 
        """
        self.original_object = [rho]
        self.object_type = "Artin representation"
        self.dim = rho.dimension()
        self.degree = self.dim
        self.weight = 0
        self.motivic_weight = 0
        self.conductor = rho.conductor()
        self.sign = rho.root_number()
        self.mu_fe = rho.mu_fe()
        self.nu_fe = rho.nu_fe()
        self.gammaV = [0 for i in range(rho.number_of_eigenvalues_plus_one_complex_conjugation())]
        for i in range(rho.number_of_eigenvalues_minus_one_complex_conjugation() ):
            self.gammaV.append(1)
        self.langlands = rho.langlands()
        self.selfdual = rho.selfdual()
        self.primitive = rho.primitive()
        self.set_dokchitser_Lfunction()
        self.set_number_of_coefficients()
        self.dirichlet_coefficients = rho.coefficients_list()
        self.coefficient_type = 0
        self.coefficient_period = 0
        self.ld.gp().quit()

    def init_elliptic_modular_form(self, F):
        """
        Initiate with an Elliptic Modular Form.
        """
        self.original_object = [F]
        self.object_type = "Elliptic Modular newform"
        self.dim = 2
        self.weight = ZZ(F.weight())
        self.motivic_weight = ZZ(F.weight()) -1
        self.conductor = F.level()
        self.langlands = True
        self.mu_fe = []
        self.nu_fe = [ZZ(F.weight()-1)/ZZ(2)]
        self.set_dokchitser_Lfunction()
        self.set_number_of_coefficients()
        self.primitive = True
        self.selfdual = True
        
        # Determining the Dirichlet coefficients. This code stolen from
        # lmfdb.lfunctions.Lfunction.Lfunction_EMF
        self.automorphyexp = (self.weight - 1) / 2.
        embeddings = F.q_expansion_embeddings(self.numcoeff + 1)
        self.algebraic_coefficients = []
        for n in range(1, self.numcoeff + 1):
            self.algebraic_coefficients.append(embeddings[n][F._fi])
            
        self.dirichlet_coefficients = []
        for n in range(1, len(self.algebraic_coefficients) + 1):
            self.dirichlet_coefficients.append(
                self.algebraic_coefficients[n-1] /
                float(n ** self.automorphyexp))
        # Need to finish here, determination of sign.
        AL = F.atkin_lehner_eigenvalues()
        self.sign = AL[self.conductor] * (-1) ** (self.weight / 2.)
        self.gammaV = [0,1] # Check with the Dokchitsers?
       # if self.selfdual:
       #     self.coefficient_type = 2
       # else:
       #     self.coefficient_type = 3
       # self.coefficient_period = chi.modulus()
        self.ld.gp().quit()


## These are used when creating the classes with the above

    def set_dokchitser_Lfunction(self):
        """
        The L-function calling Dokchitser's code
        """
        if hasattr(self, "sign"):
            # print type(self.sign)
            # type complex would yield an error here.
            self.ld = Dokchitser(conductor = self.conductor,
                                gammaV = self.gammaV,
                                weight = self.motivic_weight,
                                eps = self.sign,
                                poles = [],
                                residues = [])
        else:
            # find the sign from the functional equation
            raise NotImplementedError


    def set_number_of_coefficients(self):
        """
        Determines the number of coefficients needed using Dokchitser's
        """
        if not hasattr(self, "ld"):
            self.set_dokchitser_Lfunction()
        # note the following line only sets all the variables in the
        # gp session of Dokchitser
        self.ld._gp_eval("MaxImaginaryPart = %s"%self.max_imaginary_part)
        self.numcoeff = self.ld.num_coeffs()

## A function that gives back a L-function class as used later

    def Lfunction(self):
        """
        The L-function object associated to this class
        """
        from lmfdb.lfunctions.Lfunction import Lfunction_TensorProduct
        return Lfunction_GaloisRep(self)

## various direct accessible functions


    def root_number(self):
        """
        Root number
        """
        return self.sign


    def dimension(self):
        """
        Dimension = Degree
        """
        return self.dim

    def weight(self):
        """
        Motivic weight
        """
        return self.motivic_weight


## Now to the L-function itself

    def lfunction(self):
        """
        This method replaces the class LFunction in lmfdb.lfunctions.Lfunction
        to generate the page for this sort of class.
        """
        self.compute_kappa_lambda_Q_from_mu_nu()

        self.title = ""
        self.texname = "L(s,\\rho)"
        self.texnamecompleteds = "\\Lambda(s,\\rho)"
        self.title = "$L(s,\\rho)$, where $\\rho$ is a Galois representation"

        self.credit = 'Workshop in Besancon, 2014'

        from lmfdb.lfunctions.Lfunction import generateSageLfunction
        generateSageLfunction(self)

    def Ltype(self):
        return "galoisrepresentation"

    def Lkey(self):
        return {"galoisrepresentation":self.title}
