# shape and geometry of specimens and microstructural objects

## Status quo geometry in NeXus:
A number of base classes for geometrical descriptions are already offered by NeXus.  
First, base classes to describe affine transformations which can be chained:  
* NXgeometry (deprecated)  
* NXtransformations  

Second, base classes and contributed classes respectively to describe geometrical primitives and shapes:
* NXcylindrical_geometry
This class can be used to describe a set of cylinders which are by design linked to the description of a detector.
With its three vertex based definition for a cylinder it does by design not offer the most storage 
efficient representation of a cylinder.

NXcylindrical_geometry complements other base classes whose status is that of contributed classes:
*NXquadric
*NXoff_geometry
The latter two classes offer possibilities to describe objects via so-called constructive solid geometry (CSG).
This is a computer aided design (CAD) approach whereby objects are described through set intersections of objects
and (their) half-spaces. Take for example a cylinder:  
Its three distinct surfaces (lateral surface, two caps) can be described as the intersection surface of three
specifically parameterized quadrics: a circular cylinder and two planes. On the contrary the volume of the object
is the intersection volume between the half-space inside the circular cylinder quadric and the half-spaces behind
both the bottom and top of the two capping planes. The circular line that is the intersection between
the top capping plane and the circular cylinder can be described as a exact this, the intersection of the two
these two objects minus its volume. 

The key strength of this design, as it is implemented in right now in NeXus is that one can combine NXquadric
instances with NXoff_geometry instances. An NXoff_geometry instance describes each possible manifold that
can be described through an OFF file (a CAD file format), i.e. usually polygon meshes or polyhedra.
* NXcsg
This class essentially encodes the logical connections between the above-described set operation of the
NXoff_geometry or NXquadric instances. More specifically, it can be used to build a graph of NXcsg instances, 
which is the constructive design graph used in this field.
More specifically the above cylinder volume would be a combination of two NXcsg instances:
The first is e.g. an intersection between the circular cylinder and a plane.
The second one is an intersection of the above resultant NXcsg instance with
an again intersect operation with the other plane.

By design, NeXus thus contains already a description for spheres, cylinders, rotated bounding boxes etc.
The usage of these tools to describe e.g. NEF polyhedra is straightforward and flexible.
The description in NeXus appeals to engineers and people knowledgable in CAD.

## The current design is not ideal for average users.

However, the above example documents which tricks are necessary to describe already something as simple
as a cylinder. Evidently, using constructive solid geometry (CSG) throughout the entire application definition
and base class design can be very cumbersome process, especially for non-experts.
By contrast, everybody understands that (provided a definition of a normal) two non-overlapping points
surplus an at least epsilon large real value as a radius can be used to define a cylinder, specifically
a possibly rotated but non-degenerated one. Therefore, we build the description of microstructures and samples
by making two proposals:

**We propose to extend NeXus with a set of complementary geometric primitives.**
Users are then free to chose which description they feel that their audience is more comfortable
working with and/or feels that this description is suffices.

# Support packing of pieces of information by design
The current design of NeXus geometry descriptors has by design right now not a method
in place for packing many instances of the same class under a single base class.
Take for instance a computer simulation which tracks the evolution of grains.
One could make each grain an own base class and thus instantiate in a file a group
with as many instances of grain base classes. This has the advantage that each
grain is clearly resolved, eventually its (surface mesh) duplicated just for the sake
of rendering purposes in an application. Alternatively one could, already by design
store only the non-duplicated properties of this grain set using an e.g. field in
a base class which stores all identifier pairs of grain boundary facets. Especially
when the number of pieces of information to store for each grain is not the same,
which is usual as grains differ in the number of vertices and faces one usually
uses a support field that encodes which portion of the array data belong to which object.
This packing of many objects' values into a single field can be advantageous.
Therefore, it makes sense to offer for primitive also a set variant of the base class.
I.e. NXcg_point and NXcg_point_set, where NXcg_point defines only one point
and NXcg_point_set a predefined number of eventually many points.

**We propose to complement base classes for geometric primitives with a set variant of the respective base class.**


Triangulated surface mesh (can be open or closed)
Cuboid
Polyhedron

Example:
