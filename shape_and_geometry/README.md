# shape and geometry of specimens and microstructural objects

## Status quo geometry in NeXus:
A number of base classes for geometrical descriptions are already offered by NeXus.  
First, base classes describing affine transformations which can be chained:  
* NXgeometry (deprecated)  
* NXtransformations  

Second, base classes and contributed classes describing geometrical primitives and shapes:  
* NXcylindrical_geometry  
This class can be used to describe a set of cylinders intricately linked by design to the  
description of a detector. With its three vertex based definition for a cylinder the base  
class does not offer by design the most storage efficient representation of a cylinder.

Furthermore, there are the contributed classes:  
*NXquadric  
*NXoff_geometry  
which offer possibilities to describe objects via so-called constructive solid geometry (CSG).  
This is a computer aided design (CAD) approach whereby objects are described through 
set operations applied to objects and half-spaces through which the objects partition
a domain in regions. 

Take for example a CSG description of a cylinder.  
We need to distinguish what we want to describe:  
* The volume  
* The volume and the surface  
* The surface  
* One surface  
* The surface including the boundary  
* Only the boundary (intersection between a cap and the lateral surface)  
With CSG set operations can be used create such descriptions:  
The three surfaces can be described as specifically parameterized quadrics.  
* Two planes (the caps)  
* One circular cylinder  
The volume and the surface of the object is for example the intersection of the  
* Interior half-space of the cylinder quadric  
* Capped by the bottom and top of the two capping planes.  

NeXus combines this with optionally with NXoff_geometry instances.  
An NXoff_geometry instance describes each possible manifold that  
can be described through an OFF file (a CAD file format), i.e. usually  
polygon meshes or polyhedra.

* NXcsg
is the class which encodes the logical connections between these instances and set operations.  
More specifically, NXcsg instances can be used to define a binary graph that is used in CSG.  

In effect, these classes equip NeXus by design with a description for spheres, cylinders,  
rotated bounding boxes. Consequently, e.g. NEF polyhedra can be defined in a straightforward  
and flexible manner. This description and tool set appeals to engineers and people  
who are knowledgable in computer aided design tools and the mathematical background.  

## However, this design is not ideal or eventually perceived too complicated for average users.  

In fact, the above example documents which tricks are necessary to describe already something  
as simple as a cylinder. Using CSG throughout the entire application definition and base class  
design can be very cumbersome especially for non-experts.  
By contrast, everybody understands that (given a definition of a unit normal) two non-overlapping points  
surplus an at least epsilon large real value as a radius can be used to define a cylinder, specifically
a (possibly) rotated but non-degenerated cylinder.  
This motivates our additions to the computational geometry capabilities of NeXus.  

**We propose to extend NeXus with a set of complementary geometric primitives.**  
Users are then choose which description they feel that their audience is most comfortable with.  

# Support packing of pieces of information by design
Currently, the above-mentioned classes have by design no method in place for packing  
many instances of the same class inside a single base class. There are relevant use cases for this though:  
Take for instance a computer simulation which tracks the evolution of grains, say hundred thousand objects.  
One could make each grain an own base class and thus instantiate a group for each instance with  
sub-ordinate fields. This has the advantage that each grain is clearly resolved.  
Eventually the (surface mesh) of the grain may be duplicated just for the sake of rendering purposes  
to scientific visualization. Alternatively one could, already by design store only the unique  
descriptors of this grain set using an e.g. field in. Especially when the number of pieces of information  
to store for each grain is not the same, which is the usual case, as grains differ in the number of  
vertices and faces a support field is used which encodes which portions of the array data belong  
to which object. This packing of many objects' values into a single field can be advantageous.  

**We propose to realize base classes by design as sets of objects.**

**TO DO**:  
Triangulated surface mesh (can be open or closed)  
Cuboid  
Polyhedron  

# Example how to use each base class:  

A few non-trivial examples for each base class follow that show their intended usage.  

