FeatureScript 3083;
import(path : "onshape/std/geometry.fs", version : "3083.0");

// Editable major airflow/exterior study for the 150 mm stage. Airflow +Y.
// The detailed split-shell STEP assembly is a separate article; its bearings,
// screws, hardware envelopes and service checks do not transfer to this feature.
function dRounded(context is Context, id is Id, w, h, r, y, x, z)
{
    const a = w / 2;
    const b = h / 2;
    const k = sqrt(0.5);
    const s = newSketchOnPlane(context, id, { "sketchPlane" :
        plane(vector(x, y, z), vector(0, -1, 0), vector(1, 0, 0)) });
    skLineSegment(s, "bottom", { "start" : vector(-a + r, -b), "end" : vector(a - r, -b) });
    skArc(s, "br", { "start" : vector(a - r, -b), "mid" : vector(a - r + r * k, -b + r - r * k), "end" : vector(a, -b + r) });
    skLineSegment(s, "right", { "start" : vector(a, -b + r), "end" : vector(a, b - r) });
    skArc(s, "tr", { "start" : vector(a, b - r), "mid" : vector(a - r + r * k, b - r + r * k), "end" : vector(a - r, b) });
    skLineSegment(s, "top", { "start" : vector(a - r, b), "end" : vector(-a + r, b) });
    skArc(s, "tl", { "start" : vector(-a + r, b), "mid" : vector(-a + r - r * k, b - r + r * k), "end" : vector(-a, b - r) });
    skLineSegment(s, "left", { "start" : vector(-a, b - r), "end" : vector(-a, -b + r) });
    skArc(s, "bl", { "start" : vector(-a, -b + r), "mid" : vector(-a + r - r * k, -b + r - r * k), "end" : vector(-a + r, -b) });
    skSolve(s);
    return qSketchRegion(id);
}
function dCylinder(context is Context, id is Id, r, y0, y1)
{
    fCylinder(context, id, { "bottomCenter" : vector(0 * millimeter, y0, 0 * millimeter),
        "topCenter" : vector(0 * millimeter, y1, 0 * millimeter), "radius" : r });
}
function dName(context is Context, q is Query, name is string)
{
    setProperty(context, { "entities" : q, "propertyType" : PropertyType.NAME, "value" : name });
}

function dCircle(context is Context, id is Id, radius, y)
{
    const s = newSketchOnPlane(context, id, { "sketchPlane" : plane(vector(0 * millimeter, y, 0 * millimeter), vector(0, -1, 0), vector(1, 0, 0)) });
    const angles = [-100, -80, -10, 10, 80, 100, 170, 190, 260];
    for (var i = 0; i < 8; i += 1)
    {
        const a = angles[i] * degree;
        const b = angles[i + 1] * degree;
        skArc(s, "arc" ~ i, { "start" : radius * vector(cos(a), sin(a)), "mid" : radius * vector(cos((a + b) / 2), sin((a + b) / 2)), "end" : radius * vector(cos(b), sin(b)) });
    }
    skSolve(s);
    return qSketchRegion(id);
}

annotation { "Feature Type Name" : "Windflow150mmAirpath" }
export const windflow150mmAirpath = defineFeature(function(context is Context, id is Id, d is map)
    precondition
    {
        annotation { "Name" : "Throat diameter" }
        isLength(d.throat, { (millimeter) : [125, 152, 156] } as LengthBoundSpec);
        annotation { "Name" : "Bell-mouth radius" }
        isLength(d.bellRadius, { (millimeter) : [8, 12, 16] } as LengthBoundSpec);
        annotation { "Name" : "Wall thickness" }
        isLength(d.wall, { (millimeter) : [2.4, 2.4, 3.2] } as LengthBoundSpec);
        annotation { "Name" : "Head height - plinth and feet add 10 mm" }
        isLength(d.headHeight, { (millimeter) : [180, 185, 190] } as LengthBoundSpec);
        annotation { "Name" : "Outlet width" }
        isLength(d.width, { (millimeter) : [96, 104, 116] } as LengthBoundSpec);
        annotation { "Name" : "Outlet height" }
        isLength(d.height, { (millimeter) : [90, 94, 102] } as LengthBoundSpec);
        annotation { "Name" : "Outlet corner radius" }
        isLength(d.corner, { (millimeter) : [2, 3, 6] } as LengthBoundSpec);
        annotation { "Name" : "Smooth contraction length" }
        isLength(d.transitionLength, { (millimeter) : [65, 85, 110] } as LengthBoundSpec);
        annotation { "Name" : "Trial stator vane thickness" }
        isLength(d.vaneThickness, { (millimeter) : [1.2, 1.2, 2] } as LengthBoundSpec);
        annotation { "Name" : "Trial stator axial length" }
        isLength(d.vaneLength, { (millimeter) : [16, 24, 30] } as LengthBoundSpec);
        annotation { "Name" : "Trial stator vane count" }
        isInteger(d.vaneCount, { (unitless) : [5, 7, 11] } as IntegerBoundSpec);
        annotation { "Name" : "Trial stator inlet angle - measure actual swirl" }
        isAngle(d.inletAngle, { (degree) : [0, 20, 30] } as AngleBoundSpec);
        annotation { "Name" : "Insert radial clearance" }
        isLength(d.clearance, { (millimeter) : [0.2, 0.3, 0.6] } as LengthBoundSpec);
        annotation { "Name" : "Boost-panel length" }
        isLength(d.panelLength, { (millimeter) : [45, 55, 65] } as LengthBoundSpec);
        annotation { "Name" : "Minimum gross outlet area ratio - not a flow rating" }
        isReal(d.areaRatio, { (unitless) : [0.75, 0.75, 0.95] } as RealBoundSpec);
        annotation { "Name" : "Absolute panel angle ceiling" }
        isAngle(d.angleCeiling, { (degree) : [8, 15, 15] } as AngleBoundSpec);
        annotation { "Name" : "Boost fraction" }
        isReal(d.boost, { (unitless) : [0, 0, 1] } as RealBoundSpec);
    }
    {
        const r = d.throat / 2;
        const t = d.wall;
        const zero = 0 * millimeter;
        const sy = 78 * millimeter;
        const ey = sy + d.vaneLength;
        const ty = ey + 2 * millimeter;
        const hy = ty + d.transitionLength;
        const front = hy + d.panelLength + 22 * millimeter;
        const cr = r + 2.4 * millimeter;
        const seatRadius = cr + 0.65 * millimeter + d.clearance / 2;
        const thetaMax = asin(d.height * (1 - d.areaRatio) / (2 * d.panelLength));
        if (thetaMax > d.angleCeiling)
            throw regenError("Closure exceeds the angle ceiling; increase minimum area or panel length.", ["areaRatio", "panelLength", "angleCeiling"]);
        if (r + d.bellRadius + t > d.headHeight / 2)
            throw regenError("Bell-mouth lip must fit the selected head height.", ["throat", "bellRadius", "headHeight"]);
        var sketches = [];
        var outer = [];
        var inner = [];
        const rows = [[zero, d.throat + 33 * millimeter, d.headHeight, 89 * millimeter],
            [60 * millimeter, d.throat + 40 * millimeter, d.headHeight, 82 * millimeter],
            [ty + 6 * millimeter, d.width + 104 * millimeter, d.headHeight, 65 * millimeter],
            [hy, d.width + 114 * millimeter, d.headHeight, 35 * millimeter],
            [front, d.width + 114 * millimeter, d.headHeight, 30 * millimeter]];
        for (var i = 0; i < size(rows); i += 1)
        {
            const a = rows[i];
            const rr = min(a[3], min(a[1], a[2]) / 2 - 0.1 * millimeter);
            const oid = id + ("outerSection" ~ i);
            const iid = id + ("innerSection" ~ i);
            outer = append(outer, dRounded(context, oid, a[1], a[2], rr, a[0], zero, zero));
            inner = append(inner, dRounded(context, iid, a[1] - 2 * t, a[2] - 2 * t, rr - t,
                min(front - t, max(t, a[0])), zero, zero));
            sketches = append(sketches, qCreatedBy(oid, EntityType.BODY));
            sketches = append(sketches, qCreatedBy(iid, EntityType.BODY));
        }
        opLoft(context, id + "outerSkin", { "profileSubqueries" : outer, "bodyType" : ToolBodyType.SOLID });
        fCuboid(context, id + "heightBox", { "corner1" : vector(-200 * millimeter, -millimeter, -d.headHeight / 2),
            "corner2" : vector(200 * millimeter, front + millimeter, d.headHeight / 2) });
        opBoolean(context, id + "heightClip", { "tools" : qUnion([qCreatedBy(id + "outerSkin", EntityType.BODY),
            qCreatedBy(id + "heightBox", EntityType.BODY)]), "operationType" : BooleanOperationType.INTERSECTION });
        const head = qCreatedBy(id + "heightClip", EntityType.BODY);
        opLoft(context, id + "innerSkin", { "profileSubqueries" : inner, "bodyType" : ToolBodyType.SOLID });

        var transitionOutside = [];
        var transitionInside = [];
        for (var i = 0; i <= 5; i += 1)
        {
            const u = i / 5;
            const ease = u * u * (3 - 2 * u);
            const y = ty + u * d.transitionLength;
            const w = d.throat * (1 - ease) + d.width * ease;
            const h = d.throat * (1 - ease) + d.height * ease;
            const rr = (r - 0.1 * millimeter) * (1 - ease) + d.corner * ease;
            const oid = id + ("transitionOutside" ~ i);
            const iid = id + ("transitionInside" ~ i);
            transitionOutside = append(transitionOutside, i == 0 ? dCircle(context, oid, r + t, y) : dRounded(context, oid, w + 2 * t, h + 2 * t, rr + t, y, zero, zero));
            transitionInside = append(transitionInside, i == 0 ? dCircle(context, iid, r, y) : dRounded(context, iid, w, h, rr, y, zero, zero));
            sketches = append(sketches, qCreatedBy(oid, EntityType.BODY));
            sketches = append(sketches, qCreatedBy(iid, EntityType.BODY));
        }
        const axialEnds = [{ "profileIndex" : 0, "vector" : vector(0, 1, 0), "magnitude" : 1 },
            { "profileIndex" : 5, "vector" : vector(0, 1, 0), "magnitude" : 1 }];
        opLoft(context, id + "flowOutside", { "profileSubqueries" : transitionOutside, "derivativeInfo" : axialEnds, "bodyType" : ToolBodyType.SOLID });
        dCylinder(context, id + "ductOutside", r + t, zero, ty + 0.02 * millimeter);
        var outletOutside = [];
        var outletInside = [];
        for (var i = 0; i < 2; i += 1)
        {
            const y = i == 0 ? hy - 0.02 * millimeter : front;
            const oid = id + ("outletOutside" ~ i);
            const iid = id + ("outletInside" ~ i);
            outletOutside = append(outletOutside, dRounded(context, oid, d.width + 2 * t, d.height + 2 * t, d.corner + t, y, zero, zero));
            // Numerical relief avoids coincident trim faces. This native study
            // has 0.02 mm extra radial clearance, unlike the checked fit article.
            outletInside = append(outletInside, dRounded(context, iid, d.width + 0.04 * millimeter,
                d.height + 0.04 * millimeter, d.corner + 0.02 * millimeter, i == 0 ? hy : front + millimeter, zero, zero));
            sketches = append(sketches, qCreatedBy(oid, EntityType.BODY));
            sketches = append(sketches, qCreatedBy(iid, EntityType.BODY));
        }
        opLoft(context, id + "outletEnvelope", { "profileSubqueries" : outletOutside, "bodyType" : ToolBodyType.SOLID });
        // Preserve the duct inside the hollow exterior by subtracting its
        // envelope from the electronics cavity before cutting that cavity.
        opBoolean(context, id + "electronicsVoid0", { "targets" : qCreatedBy(id + "innerSkin", EntityType.BODY), "tools" : qCreatedBy(id + "ductOutside", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        opBoolean(context, id + "electronicsVoid1", { "targets" : qCreatedBy(id + "innerSkin", EntityType.BODY), "tools" : qCreatedBy(id + "flowOutside", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        opBoolean(context, id + "electronicsVoid2", { "targets" : qCreatedBy(id + "innerSkin", EntityType.BODY), "tools" : qCreatedBy(id + "outletEnvelope", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        opBoolean(context, id + "hollowExterior", { "targets" : head, "tools" : qCreatedBy(id + "innerSkin", EntityType.BODY),
            "operationType" : BooleanOperationType.SUBTRACTION });
        dCylinder(context, id + "throatTool", r, -millimeter, ty + 0.02 * millimeter);
        opBoolean(context, id + "throatCut", { "targets" : head, "tools" : qCreatedBy(id + "throatTool", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        opLoft(context, id + "transitionTool", { "profileSubqueries" : transitionInside, "derivativeInfo" : axialEnds, "bodyType" : ToolBodyType.SOLID });
        opBoolean(context, id + "transitionCut", { "targets" : head, "tools" : qCreatedBy(id + "transitionTool", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        opLoft(context, id + "outletTool", { "profileSubqueries" : outletInside, "bodyType" : ToolBodyType.SOLID });
        opBoolean(context, id + "outletCut", { "targets" : head, "tools" : qCreatedBy(id + "outletTool", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });

        dCylinder(context, id + "carrierCollar", seatRadius + t, 54 * millimeter, 64 * millimeter);
        opBoolean(context, id + "carrierCollarJoin", { "tools" : qUnion([head, qCreatedBy(id + "carrierCollar", EntityType.BODY)]), "operationType" : BooleanOperationType.UNION });
        dCylinder(context, id + "carrierSeat", seatRadius, 55.6 * millimeter, 62.4 * millimeter);
        dCylinder(context, id + "collarThroat", r, 53.9 * millimeter, 64.1 * millimeter);
        opBoolean(context, id + "collarBores", { "targets" : head,
            "tools" : qUnion([qCreatedBy(id + "carrierSeat", EntityType.BODY), qCreatedBy(id + "collarThroat", EntityType.BODY)]), "operationType" : BooleanOperationType.SUBTRACTION });
        dCylinder(context, id + "statorCollar", r + 4.7 * millimeter, sy - millimeter, ey + millimeter);
        opBoolean(context, id + "statorCollarJoin", { "tools" : qUnion([head, qCreatedBy(id + "statorCollar", EntityType.BODY)]), "operationType" : BooleanOperationType.UNION });
        dCylinder(context, id + "statorSeat", r + 2 * millimeter + d.clearance, sy - d.clearance, ey + d.clearance);
        dCylinder(context, id + "statorThroat", r, sy - 1.1 * millimeter, ey + 1.1 * millimeter);
        opBoolean(context, id + "statorSeatCut", { "targets" : head, "tools" : qUnion([
            qCreatedBy(id + "statorSeat", EntityType.BODY), qCreatedBy(id + "statorThroat", EntityType.BODY)]), "operationType" : BooleanOperationType.SUBTRACTION });

        // Profile reference apertures; the detailed assembly carries the real
        // screen cradle, wheel mount, split seam and purchased components.
        const screenZ = -d.headHeight / 2 + 22 * millimeter;
        fCuboid(context, id + "screenOpening", { "corner1" : vector(-21.5 * millimeter, front - t - millimeter, screenZ - 19 * millimeter),
            "corner2" : vector(41.5 * millimeter, front + millimeter, screenZ + 19 * millimeter) });
        fCylinder(context, id + "wheelOpening", { "bottomCenter" : vector(-56 * millimeter, front - t - millimeter, screenZ),
            "topCenter" : vector(-56 * millimeter, front + millimeter, screenZ), "radius" : 15.8 * millimeter });
        opBoolean(context, id + "frontControls", { "targets" : head, "tools" : qUnion([
            qCreatedBy(id + "screenOpening", EntityType.BODY), qCreatedBy(id + "wheelOpening", EntityType.BODY)]), "operationType" : BooleanOperationType.SUBTRACTION });
        dName(context, head, "Rev D native flowing hollow airpath - design study");

        const b = d.bellRadius;
        const k = sqrt(0.5);
        const bellSketch = id + "bellSection";
        const s = newSketchOnPlane(context, bellSketch, { "sketchPlane" : plane(vector(0, 0, 0) * millimeter, vector(0, 0, 1)) });
        skArc(s, "inner", { "start" : vector(r, zero), "mid" : vector(r + b - b * k, -b * k), "end" : vector(r + b, -b) });
        skLineSegment(s, "lip", { "start" : vector(r + b, -b), "end" : vector(r + b, -b + t) });
        skArc(s, "outer", { "start" : vector(r + b, -b + t), "mid" : vector(r + b - (b - t) * k, -(b - t) * k), "end" : vector(r + t, zero) });
        skLineSegment(s, "end", { "start" : vector(r + t, zero), "end" : vector(r, zero) });
        skSolve(s);
        opRevolve(context, id + "bell", { "entities" : qSketchRegion(bellSketch),
            "axis" : line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), "angleForward" : 360 * degree });
        sketches = append(sketches, qCreatedBy(bellSketch, EntityType.BODY));
        dName(context, qCreatedBy(id + "bell", EntityType.BODY), "Rev D native R" ~ (b / millimeter) ~ " rounded inlet - study");

        dCylinder(context, id + "carrierOuter", cr, 56 * millimeter, 62 * millimeter);
        dCylinder(context, id + "carrierInner", r - 1.4 * millimeter, 55.9 * millimeter, 62.1 * millimeter);
        opBoolean(context, id + "carrierRing", { "targets" : qCreatedBy(id + "carrierOuter", EntityType.BODY),
            "tools" : qCreatedBy(id + "carrierInner", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        dCylinder(context, id + "motorPlate", 20 * millimeter, 56 * millimeter, 62 * millimeter);
        var carrier = [qCreatedBy(id + "carrierOuter", EntityType.BODY), qCreatedBy(id + "motorPlate", EntityType.BODY)];
        for (var i = 0; i < 4; i += 1)
        {
            const sid = id + ("support" ~ i);
            fCuboid(context, sid, { "corner1" : vector(19 * millimeter, 56 * millimeter, -1.6 * millimeter), "corner2" : vector(cr, 62 * millimeter, 1.6 * millimeter) });
            opTransform(context, id + ("supportTurn" ~ i), { "bodies" : qCreatedBy(sid, EntityType.BODY),
                "transform" : rotationAround(line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), (45 + i * 90) * degree) });
            carrier = append(carrier, qCreatedBy(sid, EntityType.BODY));
        }
        opBoolean(context, id + "carrierJoin", { "tools" : qUnion(carrier), "operationType" : BooleanOperationType.UNION });
        const carrierBody = qCreatedBy(id + "carrierOuter", EntityType.BODY);
        for (var i = 0; i < 4; i += 1)
        {
            const a = i * 90 * degree;
            const sid = id + ("motorScrew" ~ i);
            fCylinder(context, sid, { "bottomCenter" : vector(8 * millimeter * cos(a), 55.9 * millimeter, 8 * millimeter * sin(a)),
                "topCenter" : vector(8 * millimeter * cos(a), 62.1 * millimeter, 8 * millimeter * sin(a)), "radius" : 1.7 * millimeter });
            opBoolean(context, id + ("motorHole" ~ i), { "targets" : carrierBody, "tools" : qCreatedBy(sid, EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        }
        dCylinder(context, id + "shaftRelief", 4 * millimeter, 55.9 * millimeter, 62.1 * millimeter);
        opBoolean(context, id + "shaftReliefCut", { "targets" : carrierBody, "tools" : qCreatedBy(id + "shaftRelief", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        dName(context, carrierBody, "Rev D native rigid carrier - M3 on diameter 16 PCD");
        dCylinder(context, id + "tpuOuter", cr + 0.65 * millimeter, 55.65 * millimeter, 62.35 * millimeter);
        dCylinder(context, id + "tpuInner", cr, 55.5 * millimeter, 62.5 * millimeter);
        opBoolean(context, id + "tpuRing", { "targets" : qCreatedBy(id + "tpuOuter", EntityType.BODY), "tools" : qCreatedBy(id + "tpuInner", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        dName(context, qCreatedBy(id + "tpuOuter", EntityType.BODY), "Rev D native TPU carrier isolation - fit study");

        dCylinder(context, id + "statorOuter", r + 2 * millimeter, sy, ey);
        dCylinder(context, id + "statorInner", r - 0.5 * millimeter, sy - 0.1 * millimeter, ey + 0.1 * millimeter);
        opBoolean(context, id + "statorRing", { "targets" : qCreatedBy(id + "statorOuter", EntityType.BODY), "tools" : qCreatedBy(id + "statorInner", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        dCylinder(context, id + "statorHub", 20 * millimeter, sy, ey);
        var stator = [qCreatedBy(id + "statorOuter", EntityType.BODY), qCreatedBy(id + "statorHub", EntityType.BODY)];
        var vaneProfiles = [];
        for (var i = 0; i <= 4; i += 1)
        {
            const u = i / 4;
            const sid = id + ("vaneSection" ~ i);
            const z = tan(d.inletAngle) * d.vaneLength * (u - 0.5 * u * u - 0.5);
            vaneProfiles = append(vaneProfiles, dRounded(context, sid, r - 19.9 * millimeter, d.vaneThickness,
                0.25 * millimeter, sy + u * d.vaneLength, (r + 19.5 * millimeter) / 2, z));
            sketches = append(sketches, qCreatedBy(sid, EntityType.BODY));
        }
        opLoft(context, id + "vane", { "profileSubqueries" : vaneProfiles, "bodyType" : ToolBodyType.SOLID });
        var transforms = [];
        var names = [];
        for (var i = 1; i < d.vaneCount; i += 1)
        {
            transforms = append(transforms, rotationAround(line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), i * 360 * degree / d.vaneCount));
            names = append(names, "vane" ~ i);
        }
        opPattern(context, id + "vanes", { "entities" : qCreatedBy(id + "vane", EntityType.BODY), "transforms" : transforms, "instanceNames" : names });
        opBoolean(context, id + "statorJoin", { "tools" : qUnion(append(append(stator, qCreatedBy(id + "vane", EntityType.BODY)), qCreatedBy(id + "vanes", EntityType.BODY))), "operationType" : BooleanOperationType.UNION });
        dCylinder(context, id + "hubCooling", 18 * millimeter, sy - 0.1 * millimeter, ey + 0.1 * millimeter);
        opBoolean(context, id + "hubCoolingCut", { "targets" : qCreatedBy(id + "statorOuter", EntityType.BODY), "tools" : qCreatedBy(id + "hubCooling", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        dName(context, qCreatedBy(id + "statorOuter", EntityType.BODY), "Rev D native curved radial stator - swirl trial");

        for (var i = 0; i < 2; i += 1)
        {
            const sign = i == 0 ? 1 : -1;
            const z = sign * d.height / 2;
            const pid = id + ("panel" ~ i);
            const sid = id + ("panelSpace" ~ i);
            fCuboid(context, sid, { "corner1" : vector(-d.width / 2 + 0.25 * millimeter, hy - 3.5 * millimeter, z - 2 * millimeter),
                "corner2" : vector(d.width / 2 - 0.25 * millimeter, hy + d.panelLength + 3.5 * millimeter, z + 2 * millimeter) });
            opBoolean(context, id + ("panelSpaceCut" ~ i), { "targets" : head, "tools" : qCreatedBy(sid, EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
            fCuboid(context, pid, { "corner1" : vector(-d.width / 2 + 0.35 * millimeter, hy, sign == 1 ? z : z - 1.6 * millimeter),
                "corner2" : vector(d.width / 2 - 0.35 * millimeter, hy + d.panelLength, sign == 1 ? z + 1.6 * millimeter : z) });
            opTransform(context, id + ("panelClose" ~ i), { "bodies" : qCreatedBy(pid, EntityType.BODY), "transform" :
                rotationAround(line(vector(zero, hy, z), vector(1, 0, 0)), -sign * thetaMax * d.boost) });
            dName(context, qCreatedBy(pid, EntityType.BODY), (i == 0 ? "Upper" : "Lower") ~ " native progressive panel - profile study");
        }
        opDeleteBodies(context, id + "cleanup", { "entities" : qUnion(sketches) });
        if (size(evaluateQuery(context, qBodyType(qCreatedBy(id, EntityType.BODY), BodyType.SOLID))) != 7)
            throw regenError("Expected seven connected study bodies; inspect the altered geometry.");
    }, { "throat" : 152 * millimeter, "bellRadius" : 12 * millimeter, "wall" : 2.4 * millimeter,
        "headHeight" : 185 * millimeter, "width" : 104 * millimeter, "height" : 94 * millimeter,
        "corner" : 3 * millimeter, "transitionLength" : 85 * millimeter, "vaneThickness" : 1.2 * millimeter,
        "vaneLength" : 24 * millimeter, "vaneCount" : 7, "inletAngle" : 20 * degree,
        "clearance" : 0.3 * millimeter, "panelLength" : 55 * millimeter, "areaRatio" : 0.75,
        "angleCeiling" : 15 * degree, "boost" : 0 });
