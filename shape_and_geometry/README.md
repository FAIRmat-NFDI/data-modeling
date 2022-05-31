# shape and geometry of specimens and microstructural objects

## Status quo computational geometry in NeXus:
NeXus already offers a number of base classes for geometrical descriptions:
First, base classes describing affine transformations which can be chained:  
* [NXtransformations](https://manual.nexusformat.org/classes/base_classes/NXtransformations.html#nxtransformations)  
* [NXgeometry (legacy)](https://manual.nexusformat.org/classes/base_classes/NXgeometry.html)  
* [NXtranslation (legacy)](https://manual.nexusformat.org/classes/base_classes/NXtranslation.html#nxtranslation)  

Second, base classes and contributed classes describing geometrical primitives and shapes:  
* [NXcylindrical_geometry](https://manual.nexusformat.org/classes/base_classes/NXcylindrical_geometry.html#nxcylindrical-geometry)  

This class can be used to describe a set of cylinders. The base class entries are by design  
making references to the description of detectors. With its three vertex based definition for a cylinder  
the base class does not offer by design the most storage efficient representation of a cylinder.  

Furthermore, there are the contributed classes:  
* [NXquadric](https://manual.nexusformat.org/classes/contributed_definitions/NXquadric.html#nxquadric)  
* [NXoff_geometry](https://manual.nexusformat.org/classes/base_classes/NXoff_geometry.html#nxoff-geometry)  
* [NXcsg https://manual.nexusformat.org/classes/contributed_definitions/NXcsg.html#nxcsg)  
* [NXsolid_geometry](https://manual.nexusformat.org/classes/contributed_definitions/NXsolid_geometry.html#nxsolid-geometry)  
which offer possibilities to describe objects via so-called constructive solid geometry (CSG).  
This is a computer aided design (CAD) approach whereby objects are described through set operations which are applied  
to objects and half-spaces through which the objects partition a domain in regions.  

Take for example a CSG description of a cylinder. We need to be precise in what we want to describe:  
* The volume  
* The volume and the surface  
* The total surface  
* One surface  (cap 1, cap 2, lateral surface)  
* The surface including the boundary  
* Only the boundary (the circle intersection between one or each cap and the lateral surface)  
With CSG set operations can be used create such descriptions:  
The three surfaces can be described as specifically parameterized quadrics.  
* Two planes (the caps)  
* One circular cylinder  

The volume including the total surface of the object is for example the intersection of the  
* Interior half-space of the cylinder quadric  
* cut with the bottom and the top half-space of the two capping planes.  

NeXus enables also to make instances of NXoff_geometry actors for the set operations. An NXoff_geometry instance  
describes each possible manifold that can be described through an [OFF file](https://de.wikipedia.org/wiki/Object_File_Format) (a CAD file format),  
i.e. usually polygon meshes or polyhedra. This enables the creation of polyhedra with curved interface segments (NEF polyhedra).  

NXsolid_geometry is the class which wraps the logical connections between the geometry instances and the applied set operations.  
More specifically, NXsolid_geometry is the root of the graph of NXcsg, NXoff_geometry instances which define a binary graph  
that is used frequently in the field of CSG to describe the constructed shape.  

In effect, these classes equip NeXus by design also with a description for simpler primitives like spheres, cylinders,  
or rotated bounding boxes. This description and tool set appeals to engineers and people who are knowledgable in using  
computer aided design (CAD) tools and people who are familiar with the mathematical background in this field.  

## However, this design is not ideal or eventually perceived as too complicated for average users.  

In fact, the above example documents which tricks are necessary to describe already something  
as simple as a cylinder. Using CSG throughout the entire application definition and base class  
design process can be cumbersome and difficult for non-experts. There are at least two possible solutions:  
* Implement an automated protocol that translates "simple" description into consistent CSG descriptions.  
* Implement convenient base classes to offer an alternative for frequently used primitives.  

We find the second approach the most appealing to start with because everybody understands that  
(given a definition of a unit normal) two non-overlapping points surplus an at least epsilon large  
real value as a radius define a cylinder. Specifically, a (possibly) rotated but non-degenerated cylinder.  
This motivates our here proposed additional base classes to complement the computational geometry 
capabilities of NeXus.  

**We propose to extend NeXus with a set of complementary geometric primitives.**  
Users are then free to choose which description they feel that their audience is most comfortable to work with.  

# Support packing of pieces of information by design
Currently, the above-mentioned classes have by design no method in place for packing many instances of the same class  
inside a single base class. There are relevant use cases for this though in computational materials science:  
Take for instance a computer simulation which tracks the evolution of grains, say hundred thousand grains.  
One could make each grain an own base class and thus instantiate a group for each instance with  
sub-ordinate fields (orientation, volume, etc., surface, eventually atoms and defects contained).  
This has the advantage that each grain is clearly resolved. Eventually it may require a duplication of pieces of information.  
This is for instance frequently the case when three-dimensional mesh data should be visualizable as these tools  
extend specific regular formatted input. A typical example is visualization of primitives using Paraview/HDF5/XDMF  
where specifically formatted support arrays are needed to instantiate the topology of the mesh without demanding  
further scripting by the user. Alternatively one could, already by design store only the unique  
descriptors of this grain set. For instance grain boundary data can be decoupled from the grains.  
This will then often trigger other types of support arrays to ensure the correct interpretation and linking of  
which mesh primitive is eventually shared as boundary between two adjoining crystals. Especially such support  
arrays are needed when the number of pieces of information are irregular. An example is that grains usually have  
a different number of edges, faces, and supporting vertices. The support array in such a case resolves which portions  
of the data array decode primitives of which object. This packing of many objects' values into a single field can be  
advantageous to promote storage in a compact and compressible manner. Essentially this reduces the number of nodes  
in the data description tree to reduce file handling costs. Details are implementation specific and thus classes for  
describing microstructure data have to be flexible enough to reflect these design considerations.

**We propose to realize base classes by design as sets of objects.**

# Open questions:  

* Individual base classes for polygon_soup, triangle_soup, triangle_mesh, quad_mesh, polyhedron_set, piecewise_linear_complex ?  
* Individual base classes for NXcg_sphere_set and NXcg_ellipsoid_set are both really needed, based on which decision do we propose convenience classes?
*
* Nesting of NXcg_point_set and NXcg_unit_normal_set, and NXcg_polygon_set inside the classes for the more complicated topology ?  
* What is the take on this one in other consortia? MarDI contact, INRIA's role?  
* Intersections less a priority?  
* Therefore may need to modify docstring to not write always disjoint but (ideally disjoint only)  
* CGAL uses circular iterators and half-edge-based descriptors to enforce uniqueness but [CGAL](https://doc.cgal.org/latest/Manual/packages.html#PkgHalfedgeDSo)  
*   but oftentimes many microstructure simulation codes do not reduce the primitive set to the unique ones for the sake of simplicity,  
*   or not use that level of sophistication in their implementation.
* Could we get an invitation for a review paper in a materials science journal as a consequence of which we could place our work  
*   as an attempt to a reconciliation what previous authors have done?
* How can we collect use cases (MatWerk and NFDI have many use cases, I feel it needs a glossary workshop for this as well but key people  
*   have limited resources to participate in such activities, again prioritization, focus should be on interoperability?  
*   Nomad MetaInfo does not go deep enough?  
* Multi-dimensionally-capable base classes, e.g. NXcg_ellipsoid_set how to solve that for d==2 and d==3 surface area/circumference length degenerate how to remain intuitive?

**TO DO**
NXms_matpoint_set

# Non-trivial examples of how to use each base class:  

A few non-trivial examples for each base class follow that show their intended usage.  

