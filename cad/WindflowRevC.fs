FeatureScript 3083;
import(path : "onshape/std/geometry.fs", version : "3083.0");

// Rev C architecture geometry. Airflow +Y, motor prop-seat Y29, mounting face Y52.
// Native adjustable solids, not a physically qualified assembly or fragment guard.
function roundedProfile(context is Context, id is Id, w, h, r, y)
{
    const a = w / 2;
    const b = h / 2;
    const k = sqrt(0.5);
    const sk = newSketchOnPlane(context, id, { "sketchPlane" : plane(vector(0 * millimeter, y, 0 * millimeter), vector(0, -1, 0), vector(1, 0, 0)) });
    skLineSegment(sk, "bottom", { "start" : vector(-a + r, -b), "end" : vector(a - r, -b) });
    skArc(sk, "br", { "start" : vector(a - r, -b), "mid" : vector(a - r + r * k, -b + r - r * k), "end" : vector(a, -b + r) });
    skLineSegment(sk, "right", { "start" : vector(a, -b + r), "end" : vector(a, b - r) });
    skArc(sk, "tr", { "start" : vector(a, b - r), "mid" : vector(a - r + r * k, b - r + r * k), "end" : vector(a - r, b) });
    skLineSegment(sk, "top", { "start" : vector(a - r, b), "end" : vector(-a + r, b) });
    skArc(sk, "tl", { "start" : vector(-a + r, b), "mid" : vector(-a + r - r * k, b - r + r * k), "end" : vector(-a, b - r) });
    skLineSegment(sk, "left", { "start" : vector(-a, b - r), "end" : vector(-a, -b + r) });
    skArc(sk, "bl", { "start" : vector(-a, -b + r), "mid" : vector(-a + r - r * k, -b + r - r * k), "end" : vector(-a + r, -b) });
    skSolve(sk);
    return qSketchRegion(id);
}
function segmentedCircle(context is Context, id is Id, radius, y)
{
    const sk = newSketchOnPlane(context, id, { "sketchPlane" : plane(vector(0 * millimeter, y, 0 * millimeter), vector(0, -1, 0), vector(1, 0, 0)) });
    const angles = [-100, -80, -10, 10, 80, 100, 170, 190, 260];
    for (var i = 0; i < 8; i += 1)
    {
        const a = angles[i] * degree;
        const b = angles[i + 1] * degree;
        const m = (a + b) / 2;
        skArc(sk, "arc" ~ i, { "start" : radius * vector(cos(a), sin(a)), "mid" : radius * vector(cos(m), sin(m)), "end" : radius * vector(cos(b), sin(b)) });
    }
    skSolve(sk);
    return qSketchRegion(id);
}
function cylinderY(context is Context, id is Id, radius, y0, y1)
{
    fCylinder(context, id, { "bottomCenter" : vector(0 * millimeter, y0, 0 * millimeter), "topCenter" : vector(0 * millimeter, y1, 0 * millimeter), "radius" : radius });
}

annotation { "Feature Type Name" : "WindflowRevCHead" }
export const windflowRevCHead = defineFeature(function(context is Context, id is Id, d is map)
    precondition
    {
        annotation { "Name" : "Rotor throat diameter" }
        isLength(d.throat, { (millimeter) : [110, 114, 140] } as LengthBoundSpec);
        annotation { "Name" : "Bell-mouth radius" }
        isLength(d.bellRadius, { (millimeter) : [8, 14, 24] } as LengthBoundSpec);
        annotation { "Name" : "Nominal wall" }
        isLength(d.wall, { (millimeter) : [2, 2.4, 4] } as LengthBoundSpec);
        annotation { "Name" : "Outlet width" }
        isLength(d.width, { (millimeter) : [95, 104, 120] } as LengthBoundSpec);
        annotation { "Name" : "Outlet height" }
        isLength(d.height, { (millimeter) : [85, 94, 110] } as LengthBoundSpec);
        annotation { "Name" : "Panel length" }
        isLength(d.panelLength, { (millimeter) : [45, 55, 65] } as LengthBoundSpec);
        annotation { "Name" : "Stator vane thickness" }
        isLength(d.vaneThickness, { (millimeter) : [1.2, 1.2, 2] } as LengthBoundSpec);
        annotation { "Name" : "Stator length" }
        isLength(d.vaneLength, { (millimeter) : [12, 18, 20] } as LengthBoundSpec);
        annotation { "Name" : "Stator vane count" }
        isInteger(d.vaneCount, { (unitless) : [5, 7, 11] } as IntegerBoundSpec);
        annotation { "Name" : "Transition length" }
        isLength(d.transitionLength, { (millimeter) : [25, 30, 45] } as LengthBoundSpec);
        annotation { "Name" : "Carrier radial clearance" }
        isLength(d.clearance, { (millimeter) : [0.2, 0.3, 0.6] } as LengthBoundSpec);
        annotation { "Name" : "Maximum panel closure angle" }
        isAngle(d.maxClosure, { (degree) : [5, 15, 15] } as AngleBoundSpec);
        annotation { "Name" : "Boost fraction" }
        isReal(d.boost, { (unitless) : [0, 0, 1] } as RealBoundSpec);
        annotation { "Name" : "Minimum gross area ratio - requires measurement" }
        isReal(d.areaRatio, { (unitless) : [0.75, 0.75, 0.95] } as RealBoundSpec);
    }
    {
        const r = d.throat / 2;
        const t = d.wall;
        const statorStart = 60 * millimeter;
        const statorEnd = statorStart + d.vaneLength;
        const transitionStart = statorEnd + 2 * millimeter;
        const nozzleStart = transitionStart + d.transitionLength;
        const front = nozzleStart + d.panelLength + 17 * millimeter;
        var outerProfiles = [];
        var innerProfiles = [];
        var sketches = [];
        const os = [[0, d.throat + 12 * millimeter, d.throat + 12 * millimeter, 52 * millimeter],
                    [52, d.throat + 14 * millimeter, d.throat + 14 * millimeter, 46 * millimeter],
                    [nozzleStart / millimeter, d.width + 16 * millimeter, d.height + 16 * millimeter, 15 * millimeter],
                    [front / millimeter, d.width + 18 * millimeter, d.height + 18 * millimeter, 10 * millimeter]];
        for (var i = 0; i < size(os); i += 1)
        {
            const sid = id + ("outerSection" ~ i);
            outerProfiles = append(outerProfiles, roundedProfile(context, sid, os[i][1], os[i][2], os[i][3], os[i][0] * millimeter));
            sketches = append(sketches, qCreatedBy(sid, EntityType.BODY));
        }
        opLoft(context, id + "outer", { "profileSubqueries" : outerProfiles, "bodyType" : BodyType.SOLID });
        for (var i = 0; i < 2; i += 1)
        {
            const sid = id + ("innerSection" ~ i);
            const y = i == 0 ? transitionStart : nozzleStart + 0.02 * millimeter;
            innerProfiles = append(innerProfiles, i == 0 ? segmentedCircle(context, sid, r, y) : roundedProfile(context, sid, d.width, d.height, 3 * millimeter, y));
            sketches = append(sketches, qCreatedBy(sid, EntityType.BODY));
        }
        opLoft(context, id + "transition", { "profileSubqueries" : innerProfiles, "bodyType" : ToolBodyType.SOLID });
        cylinderY(context, id + "throatTool", r, -millimeter, transitionStart + 0.02 * millimeter);
        // 0.02 mm radial offset avoids coincident cut faces at the blend join.
        const outletProfile0 = roundedProfile(context, id + "outlet0", d.width + 0.04 * millimeter, d.height + 0.04 * millimeter, 3.02 * millimeter, nozzleStart);
        const outletProfile1 = roundedProfile(context, id + "outlet1", d.width + 0.04 * millimeter, d.height + 0.04 * millimeter, 3.02 * millimeter, front + millimeter);
        sketches = append(sketches, qCreatedBy(id + "outlet0", EntityType.BODY));
        sketches = append(sketches, qCreatedBy(id + "outlet1", EntityType.BODY));
        opLoft(context, id + "outletTool", { "profileSubqueries" : [outletProfile0, outletProfile1], "bodyType" : ToolBodyType.SOLID });
        opBoolean(context, id + "throatCut", { "targets" : qCreatedBy(id + "outer", EntityType.BODY), "tools" : qCreatedBy(id + "throatTool", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        opBoolean(context, id + "transitionCut", { "targets" : qCreatedBy(id + "outer", EntityType.BODY), "tools" : qCreatedBy(id + "transition", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        opBoolean(context, id + "outletCut", { "targets" : qCreatedBy(id + "outer", EntityType.BODY), "tools" : qCreatedBy(id + "outletTool", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });

        // Receiver bore for the separate motor carrier, 0.30 mm radial allowance.
        cylinderY(context, id + "carrierSeat", r + 2.4 * millimeter + d.clearance, 52 * millimeter - d.clearance, 58 * millimeter + d.clearance);
        opBoolean(context, id + "carrierSeatCut", { "targets" : qCreatedBy(id + "outer", EntityType.BODY), "tools" : qCreatedBy(id + "carrierSeat", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        setProperty(context, { "entities" : qCreatedBy(id + "outer", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "Rev C flowing integral outlet shell - development" });

        // True rounded inlet section. Separate insert permits inlet comparison.
        const b = d.bellRadius;
        const k = sqrt(0.5);
        const sk = newSketchOnPlane(context, id + "bellSection", { "sketchPlane" : plane(vector(0, 0, 0) * millimeter, vector(0, 0, 1)) });
        skArc(sk, "inner", { "start" : vector(r, 0 * millimeter), "mid" : vector(r + b - b * k, -b * k), "end" : vector(r + b, -b) });
        skLineSegment(sk, "lip", { "start" : vector(r + b, -b), "end" : vector(r + b, -b + t) });
        skArc(sk, "outer", { "start" : vector(r + b, -b + t), "mid" : vector(r + b - (b - t) * k, -(b - t) * k), "end" : vector(r + t, 0 * millimeter) });
        skLineSegment(sk, "end", { "start" : vector(r + t, 0 * millimeter), "end" : vector(r, 0 * millimeter) });
        skSolve(sk);
        opRevolve(context, id + "bell", { "entities" : qSketchRegion(id + "bellSection"), "axis" : line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), "angleForward" : 360 * degree });
        sketches = append(sketches, qCreatedBy(id + "bellSection", EntityType.BODY));
        setProperty(context, { "entities" : qCreatedBy(id + "bell", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "Rev C R14 bell-mouth - development" });

        // Motor carrier: four circular-PCD screw positions and rigid central web.
        cylinderY(context, id + "carrierOuter", r + 2.4 * millimeter, 52 * millimeter, 58 * millimeter);
        cylinderY(context, id + "carrierInner", r - 1.6 * millimeter, 52 * millimeter, 58 * millimeter);
        opBoolean(context, id + "carrierRing", { "targets" : qCreatedBy(id + "carrierOuter", EntityType.BODY), "tools" : qCreatedBy(id + "carrierInner", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        cylinderY(context, id + "motorPlate", 18 * millimeter, 52 * millimeter, 58 * millimeter);
        var carrier = [qCreatedBy(id + "carrierOuter", EntityType.BODY), qCreatedBy(id + "motorPlate", EntityType.BODY)];
        for (var i = 0; i < 4; i += 1)
        {
            const sid = id + ("support" ~ i);
            fCuboid(context, sid, { "corner1" : vector(17 * millimeter, 52 * millimeter, -1.6 * millimeter), "corner2" : vector(r + 2.4 * millimeter, 58 * millimeter, 1.6 * millimeter) });
            opTransform(context, id + ("supportTurn" ~ i), { "bodies" : qCreatedBy(sid, EntityType.BODY), "transform" : rotationAround(line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), (45 + i * 90) * degree) });
            carrier = append(carrier, qCreatedBy(sid, EntityType.BODY));
        }
        opBoolean(context, id + "carrierJoin", { "tools" : qUnion(carrier), "operationType" : BooleanOperationType.UNION });
        for (var i = 0; i < 4; i += 1)
        {
            const a = i * 90 * degree;
            const x = 8 * millimeter * cos(a);
            const z = 8 * millimeter * sin(a);
            const sid = id + ("motorScrew" ~ i);
            fCylinder(context, sid, { "bottomCenter" : vector(x, 51.9 * millimeter, z), "topCenter" : vector(x, 58.1 * millimeter, z), "radius" : 1.7 * millimeter });
            opBoolean(context, id + ("motorHole" ~ i), { "targets" : qCreatedBy(id + "carrierOuter", EntityType.BODY), "tools" : qCreatedBy(sid, EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        }
        cylinderY(context, id + "motorShaftRelief", 4 * millimeter, 51.9 * millimeter, 58.1 * millimeter);
        opBoolean(context, id + "motorReliefCut", { "targets" : qCreatedBy(id + "carrierOuter", EntityType.BODY), "tools" : qCreatedBy(id + "motorShaftRelief", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        setProperty(context, { "entities" : qCreatedBy(id + "carrierOuter", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "Rev C motor carrier - Ø16 PCD - development" });
        cylinderY(context, id + "motorBell", 15.1 * millimeter, 29 * millimeter, 52 * millimeter);
        cylinderY(context, id + "motorShaft", 2.5 * millimeter, 21 * millimeter, 29 * millimeter);
        opBoolean(context, id + "motorReference", { "tools" : qUnion([qCreatedBy(id + "motorBell", EntityType.BODY), qCreatedBy(id + "motorShaft", EntityType.BODY)]), "operationType" : BooleanOperationType.UNION });
        setProperty(context, { "entities" : qCreatedBy(id + "motorBell", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "REF-P2406 drawing envelope - seat position unverified" });

        // Separate stator trial, with a motor-cooling annulus and printable vanes.
        cylinderY(context, id + "statorOuter", r - d.clearance, statorStart, statorEnd);
        cylinderY(context, id + "statorInner", r - d.clearance - d.vaneThickness, statorStart, statorEnd);
        opBoolean(context, id + "statorRing", { "targets" : qCreatedBy(id + "statorOuter", EntityType.BODY), "tools" : qCreatedBy(id + "statorInner", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        cylinderY(context, id + "statorHub", 18 * millimeter, statorStart, statorEnd);
        var stator = [qCreatedBy(id + "statorOuter", EntityType.BODY), qCreatedBy(id + "statorHub", EntityType.BODY)];
        for (var i = 0; i < d.vaneCount; i += 1)
        {
            const sid = id + ("statorVane" ~ i);
            fCuboid(context, sid, { "corner1" : vector(17.5 * millimeter, statorStart, -d.vaneThickness / 2), "corner2" : vector(r - d.clearance, statorEnd, d.vaneThickness / 2) });
            opTransform(context, id + ("statorTurn" ~ i), { "bodies" : qCreatedBy(sid, EntityType.BODY), "transform" : rotationAround(line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), i * 360 * degree / d.vaneCount) });
            stator = append(stator, qCreatedBy(sid, EntityType.BODY));
        }
        opBoolean(context, id + "statorJoin", { "tools" : qUnion(stator), "operationType" : BooleanOperationType.UNION });
        cylinderY(context, id + "statorCoolingHole", 16 * millimeter, statorStart - 0.1 * millimeter, statorEnd + 0.1 * millimeter);
        opBoolean(context, id + "statorCoolingCut", { "targets" : qCreatedBy(id + "statorOuter", EntityType.BODY), "tools" : qCreatedBy(id + "statorCoolingHole", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        setProperty(context, { "entities" : qCreatedBy(id + "statorOuter", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "Rev C stator trial - compare with open spacer" });

        // Panel bodies are a motion study; their corner/service mechanism follows.
        const theta = min(asin(d.height * (1 - d.areaRatio) / (2 * d.panelLength)), d.maxClosure) * d.boost;
        for (var i = 0; i < 2; i += 1)
        {
            const sign = i == 0 ? 1 : -1;
            // Match the local mechanism's air-facing planes and hinge axes.
            // The skin lies outboard in normal mode; a real shell slot clears
            // it rather than introducing a fixed restriction at the opening.
            const z = sign * d.height / 2;
            const reliefId = id + ("panelRelief" ~ i);
            fCuboid(context, reliefId, { "corner1" : vector(-d.width / 2 + 0.25 * millimeter, nozzleStart - 3.5 * millimeter, z - 2 * millimeter), "corner2" : vector(d.width / 2 - 0.25 * millimeter, nozzleStart + d.panelLength + 3.5 * millimeter, z + 2 * millimeter) });
            opBoolean(context, id + ("panelReliefCut" ~ i), { "targets" : qCreatedBy(id + "outer", EntityType.BODY), "tools" : qCreatedBy(reliefId, EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
            const pid = id + ("panel" ~ i);
            fCuboid(context, pid, { "corner1" : vector(-d.width / 2 + d.clearance + 0.05 * millimeter, nozzleStart, sign == 1 ? z : z - 1.6 * millimeter), "corner2" : vector(d.width / 2 - d.clearance - 0.05 * millimeter, nozzleStart + d.panelLength, sign == 1 ? z + 1.6 * millimeter : z) });
            opTransform(context, id + ("panelClose" ~ i), { "bodies" : qCreatedBy(pid, EntityType.BODY), "transform" : rotationAround(line(vector(0 * millimeter, nozzleStart, z), vector(1, 0, 0)), -sign * theta) });
            setProperty(context, { "entities" : qCreatedBy(pid, EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : (i == 0 ? "Upper" : "Lower") ~ " Rev C boost panel motion study" });
        }

        // A curved base replaces the vertical rectangular electronics box.
        const base0 = roundedProfile(context, id + "base0", 190 * millimeter, 175 * millimeter, 20 * millimeter, 0 * millimeter);
        const base1 = roundedProfile(context, id + "base1", 190 * millimeter, 175 * millimeter, 20 * millimeter, 6 * millimeter);
        const base2 = roundedProfile(context, id + "base2", 184 * millimeter, 160 * millimeter, 22 * millimeter, 44 * millimeter);
        opLoft(context, id + "baseOuter", { "profileSubqueries" : [base0, base1, base2], "bodyType" : ToolBodyType.SOLID });
        const baseInner0 = roundedProfile(context, id + "baseInner0", 184 * millimeter, 169 * millimeter, 17 * millimeter, -millimeter);
        const baseInner1 = roundedProfile(context, id + "baseInner1", 178 * millimeter, 154 * millimeter, 19 * millimeter, 41 * millimeter);
        opLoft(context, id + "baseInner", { "profileSubqueries" : [baseInner0, baseInner1], "bodyType" : ToolBodyType.SOLID });
        opBoolean(context, id + "baseHollow", { "targets" : qCreatedBy(id + "baseOuter", EntityType.BODY), "tools" : qCreatedBy(id + "baseInner", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        opTransform(context, id + "basePlace", { "bodies" : qCreatedBy(id + "baseOuter", EntityType.BODY), "transform" : transform(vector(0, 84, -118) * millimeter) * rotationAround(line(vector(0, 0, 0) * millimeter, vector(1, 0, 0)), 90 * degree) });
        fCuboid(context, id + "screenWindow", { "corner1" : vector(-31 * millimeter, 155 * millimeter, -114 * millimeter), "corner2" : vector(31 * millimeter, 179 * millimeter, -77 * millimeter) });
        opBoolean(context, id + "screenWindowCut", { "targets" : qCreatedBy(id + "baseOuter", EntityType.BODY), "tools" : qCreatedBy(id + "screenWindow", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        setProperty(context, { "entities" : qCreatedBy(id + "baseOuter", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "Rev C flowing electronics base - mount integration pending" });
        for (var i = 0; i < 5; i += 1)
        {
            const sid = id + (["base0", "base1", "base2", "baseInner0", "baseInner1"][i]);
            sketches = append(sketches, qCreatedBy(sid, EntityType.BODY));
        }

        // Rounded external side fairing: preserves a separate service part.
        const cover0 = roundedProfile(context, id + "cover0", 112 * millimeter, 148 * millimeter, 18 * millimeter, 0 * millimeter);
        const cover1 = roundedProfile(context, id + "cover1", 108 * millimeter, 138 * millimeter, 30 * millimeter, 12 * millimeter);
        const cover2 = roundedProfile(context, id + "cover2", 96 * millimeter, 112 * millimeter, 35 * millimeter, 28 * millimeter);
        opLoft(context, id + "coverOuter", { "profileSubqueries" : [cover0, cover1, cover2], "bodyType" : ToolBodyType.SOLID });
        const coverInner0 = roundedProfile(context, id + "coverInner0", 106 * millimeter, 142 * millimeter, 15 * millimeter, -millimeter);
        const coverInner1 = roundedProfile(context, id + "coverInner1", 90 * millimeter, 106 * millimeter, 32 * millimeter, 25 * millimeter);
        opLoft(context, id + "coverInner", { "profileSubqueries" : [coverInner0, coverInner1], "bodyType" : ToolBodyType.SOLID });
        opBoolean(context, id + "coverHollow", { "targets" : qCreatedBy(id + "coverOuter", EntityType.BODY), "tools" : qCreatedBy(id + "coverInner", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        // Local profile X -> global Z, profile Z -> -global Y, depth -> global X.
        const coverRotation = rotationAround(line(vector(0, 0, 0) * millimeter, vector(1, 1, 1)), -120 * degree);
        opTransform(context, id + "coverPlace", { "bodies" : qCreatedBy(id + "coverOuter", EntityType.BODY), "transform" : transform(vector(60, 96, -18) * millimeter) * coverRotation });
        opBoolean(context, id + "coverHeadRelief", { "targets" : qCreatedBy(id + "coverOuter", EntityType.BODY), "tools" : qCreatedBy(id + "outer", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION, "keepTools" : true });
        setProperty(context, { "entities" : qCreatedBy(id + "coverOuter", EntityType.BODY), "propertyType" : PropertyType.NAME, "value" : "Rev C flowing linkage fairing - mechanism fit pending" });
        for (var i = 0; i < 5; i += 1)
        {
            const sid = id + (["cover0", "cover1", "cover2", "coverInner0", "coverInner1"][i]);
            sketches = append(sketches, qCreatedBy(sid, EntityType.BODY));
        }
        opSplitPart(context, id + "splitHead", { "targets" : qCreatedBy(id + "outer", EntityType.BODY), "tool" : plane(vector(0, 0, 0) * millimeter, vector(1, 0, 0)), "keepType" : SplitOperationKeepType.KEEP_ALL });
        opDeleteBodies(context, id + "cleanup", { "entities" : qUnion(sketches) });
    }, { "throat" : 114 * millimeter, "bellRadius" : 14 * millimeter, "wall" : 2.4 * millimeter, "width" : 104 * millimeter, "height" : 94 * millimeter, "panelLength" : 55 * millimeter, "vaneThickness" : 1.2 * millimeter, "vaneLength" : 18 * millimeter, "vaneCount" : 7, "transitionLength" : 30 * millimeter, "clearance" : 0.3 * millimeter, "maxClosure" : 15 * degree, "boost" : 0, "areaRatio" : 0.75 });
