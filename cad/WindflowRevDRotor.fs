FeatureScript 3083;
import(path : "onshape/std/geometry.fs", version : "3083.0");

// Adjustable native rotor study. The independently checked P2 exchange rotor
// has denser, ruled root-blend stations and a rounded hub. It remains the fit
// article. This native profile study is not print or operating qualification.
function rotorSection(context is Context, id is Id, radius, chord, thickness,
                      lead, trail, camber, sweep, pitch)
{
    const tangent = vector(-cos(pitch) * sin(sweep), sin(pitch), cos(pitch) * cos(sweep));
    const sk = newSketchOnPlane(context, id, { "sketchPlane" :
        plane(vector(radius * cos(sweep), 20 * millimeter, radius * sin(sweep)),
              vector(-cos(sweep), 0, -sin(sweep)), tangent) });
    const front = -chord / 2 + lead;
    const rear = chord / 2 - trail;
    skFitSpline(sk, "upper", { "points" : [vector(front, lead),
        vector(-chord * 0.24, thickness / 2 + camber),
        vector(chord * 0.10, thickness * 0.46 + camber),
        vector(chord * 0.28, thickness * 0.34 + camber * 0.5), vector(rear, trail)],
        "startDerivative" : vector(chord, 0 * millimeter),
        "endDerivative" : vector(chord, 0 * millimeter) });
    skArc(sk, "tail", { "start" : vector(rear, trail), "mid" : vector(chord / 2, 0 * millimeter), "end" : vector(rear, -trail) });
    skFitSpline(sk, "lower", { "points" : [vector(rear, -trail),
        vector(chord * 0.28, -thickness * 0.34 + camber * 0.5),
        vector(chord * 0.10, -thickness * 0.46 + camber),
        vector(-chord * 0.24, -thickness / 2 + camber), vector(front, -lead)],
        "startDerivative" : vector(-chord, 0 * millimeter),
        "endDerivative" : vector(-chord, 0 * millimeter) });
    skArc(sk, "nose", { "start" : vector(front, -lead), "mid" : vector(-chord / 2, 0 * millimeter), "end" : vector(front, lead) });
    skSolve(sk);
    return qSketchRegion(id);
}

annotation { "Feature Type Name" : "Windflow150SweptRotor" }
export const windflow150SweptRotor = defineFeature(function(context is Context, id is Id, d is map)
    precondition
    {
        annotation { "Name" : "Rotor diameter - development only" }
        isLength(d.diameter, { (millimeter) : [125, 150, 154] } as LengthBoundSpec);
        annotation { "Name" : "Blade count - compare equal solidity" }
        isInteger(d.bladeCount, { (unitless) : [5, 5, 7] } as IntegerBoundSpec);
        annotation { "Name" : "Chord multiplier" }
        isReal(d.chordScale, { (unitless) : [0.65, 1, 1.15] } as RealBoundSpec);
        annotation { "Name" : "Forward sweep multiplier" }
        isReal(d.sweepScale, { (unitless) : [0, 1, 1.25] } as RealBoundSpec);
        annotation { "Name" : "Pitch design RPM - not an operating limit" }
        isInteger(d.designRPM, { (unitless) : [1000, 2200, 4000] } as IntegerBoundSpec);
        annotation { "Name" : "Pitch design axial speed in m/s - not a prediction" }
        isReal(d.axialVelocity, { (unitless) : [2, 5, 8] } as RealBoundSpec);
        annotation { "Name" : "Geometric incidence" }
        isAngle(d.incidence, { (degree) : [0, 5, 10] } as AngleBoundSpec);
    }
    {
        // Radius/chord/thickness/LE radius/TE radius/camber/sweep; mm and degrees.
        const rows = [[16,28,6.5,1.8,1,0.8,0], [20,30,6.5,1.8,1,0.8,0],
                      [23,31,5.6,1.6,0.8,1,0], [30,33,4.8,1.4,0.65,1.15,0.4],
                      [42,34,4.2,1.2,0.5,1.15,1.8], [55,31,3.5,1,0.45,1,4.2],
                      [66,26,2.8,0.9,0.4,0.8,6.7], [75,20,2.4,0.8,0.4,0.55,8]];
        var profiles = [];
        var sketches = [];
        for (var i = 0; i < size(rows); i += 1)
        {
            const a = rows[i];
            const radius = (a[0] <= 20 ? a[0] * millimeter :
                20 * millimeter + (a[0] - 20) * (d.diameter - 40 * millimeter) / 110);
            const pitch = atan2(d.axialVelocity, d.designRPM * 2 * PI / 60 * (radius / meter)) + d.incidence;
            const sid = id + ("section" ~ i);
            profiles = append(profiles, rotorSection(context, sid, radius,
                a[1] * d.chordScale * millimeter, a[2] * millimeter, a[3] * millimeter,
                a[4] * millimeter, a[5] * millimeter, a[6] * d.sweepScale * degree, pitch));
            sketches = append(sketches, qCreatedBy(sid, EntityType.BODY));
        }
        opLoft(context, id + "blade", { "profileSubqueries" : profiles, "bodyType" : ToolBodyType.SOLID });
        fCylinder(context, id + "tipEnvelope", { "bottomCenter" : vector(0, 0.5, 0) * millimeter,
            "topCenter" : vector(0, 40, 0) * millimeter, "radius" : d.diameter / 2 });
        opBoolean(context, id + "tipTrim", {
            "tools" : qUnion([qCreatedBy(id + "blade", EntityType.BODY), qCreatedBy(id + "tipEnvelope", EntityType.BODY)]),
            "operationType" : BooleanOperationType.INTERSECTION });
        var transforms = [];
        var instanceNames = [];
        for (var i = 1; i < d.bladeCount; i += 1)
        {
            transforms = append(transforms, rotationAround(line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), i * 360 * degree / d.bladeCount));
            instanceNames = append(instanceNames, "blade" ~ i);
        }
        const trimmedBlade = qCreatedBy(id + "tipTrim", EntityType.BODY);
        opPattern(context, id + "blades", { "entities" : trimmedBlade,
            "transforms" : transforms, "instanceNames" : instanceNames });
        fCylinder(context, id + "hub", { "bottomCenter" : vector(0, 0, 0) * millimeter,
            "topCenter" : vector(0, 40, 0) * millimeter, "radius" : 20 * millimeter });
        opBoolean(context, id + "join", { "tools" : qUnion([qCreatedBy(id + "hub", EntityType.BODY),
            trimmedBlade, qCreatedBy(id + "blades", EntityType.BODY)]),
            "operationType" : BooleanOperationType.UNION });
        const rotor = qCreatedBy(id + "hub", EntityType.BODY);
        fCylinder(context, id + "nutAccess", { "bottomCenter" : vector(0, 2.5, 0) * millimeter,
            "topCenter" : vector(0, 40.1, 0) * millimeter, "radius" : 7.25 * millimeter });
        fCylinder(context, id + "shaft", { "bottomCenter" : vector(0, -0.1, 0) * millimeter,
            "topCenter" : vector(0, 40.1, 0) * millimeter, "radius" : 2.6 * millimeter });
        opBoolean(context, id + "hubCut", { "targets" : rotor,
            "tools" : qUnion([qCreatedBy(id + "nutAccess", EntityType.BODY), qCreatedBy(id + "shaft", EntityType.BODY)]),
            "operationType" : BooleanOperationType.SUBTRACTION });
        opTransform(context, id + "installed", { "bodies" : rotor,
            "transform" : transform(vector(0, 33, 0) * millimeter) *
                rotationAround(line(vector(0, 0, 0) * millimeter, vector(1, 0, 0)), 180 * degree) });
        setProperty(context, { "entities" : rotor, "propertyType" : PropertyType.NAME,
            "value" : "150 mm native swept rotor profile study - NO SPIN RELEASE" });
        opDeleteBodies(context, id + "cleanSketches", { "entities" : qUnion(sketches) });
    }, { "diameter" : 150 * millimeter, "bladeCount" : 5, "chordScale" : 1,
         "sweepScale" : 1, "designRPM" : 2200, "axialVelocity" : 5, "incidence" : 5 * degree });
