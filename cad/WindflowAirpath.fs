FeatureScript 3044;
import(path : "onshape/std/geometry.fs", version : "3044.0");

// Windflow native parametric components. Compiled and instantiated in the
// Rev B native airflow Part Studio; two successful bodies verified 2026-10-03.
// Airflow is +Y. Dimensions match parameters.json and the local housing model.

annotation { "Feature Type Name" : "Windflow bell-mouth" }
export const windflowBellmouth = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Throat diameter" }
        isLength(definition.throat, { (millimeter) : [80, 114, 160] } as LengthBoundSpec);
        annotation { "Name" : "Bell-mouth radius" }
        isLength(definition.radius, { (millimeter) : [5, 14, 30] } as LengthBoundSpec);
        annotation { "Name" : "Wall thickness" }
        isLength(definition.wall, { (millimeter) : [1.2, 2.4, 4] } as LengthBoundSpec);
        annotation { "Name" : "Throat plane Y" }
        isLength(definition.throatY, { (millimeter) : [-100, -2.4, 100] } as LengthBoundSpec);
    }
    {
        if (definition.radius <= definition.wall)
            throw regenError("Bell-mouth radius must exceed wall thickness.", ["radius", "wall"]);
        const r = definition.throat / 2;
        const b = definition.radius;
        const t = definition.wall;
        const y = definition.throatY;
        const k = sqrt(0.5);
        const sk = newSketchOnPlane(context, id + "section", {
            "sketchPlane" : plane(vector(0, 0, 0) * millimeter, vector(0, 0, 1)) });
        skArc(sk, "inner", { "start" : vector(r, y),
            "mid" : vector(r + b - b * k, y - b * k), "end" : vector(r + b, y - b) });
        skLineSegment(sk, "lip", { "start" : vector(r + b, y - b), "end" : vector(r + b, y - b + t) });
        skArc(sk, "outer", { "start" : vector(r + b, y - b + t),
            "mid" : vector(r + b - (b - t) * k, y - (b - t) * k), "end" : vector(r + t, y) });
        skLineSegment(sk, "throat", { "start" : vector(r + t, y), "end" : vector(r, y) });
        skSolve(sk);
        opRevolve(context, id + "revolve", { "entities" : qSketchRegion(id + "section"),
            "axis" : line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), "angleForward" : 360 * degree });
        opDeleteBodies(context, id + "cleanup", { "entities" : qCreatedBy(id + "section", EntityType.BODY) });
        setProperty(context, { "entities" : qCreatedBy(id + "revolve", EntityType.BODY),
            "propertyType" : PropertyType.NAME, "value" : "Parametric bell-mouth R" ~ (b / millimeter) });
    });

// Editable aerodynamic mechanism geometry. The imported product assembly still
// carries its complete bearings, keyed cranks and fasteners; this native feature
// exposes the section, panel motion and safety limits for direct design studies.
annotation { "Feature Type Name" : "Windflow progressive nozzle" }
export const windflowProgressiveNozzle = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Clear outlet width" }
        isLength(definition.width, { (millimeter) : [80, 104, 140] } as LengthBoundSpec);
        annotation { "Name" : "Clear outlet height" }
        isLength(definition.height, { (millimeter) : [70, 94, 130] } as LengthBoundSpec);
        annotation { "Name" : "Nozzle length" }
        isLength(definition.nozzleLength, { (millimeter) : [45, 65, 100] } as LengthBoundSpec);
        annotation { "Name" : "Panel length" }
        isLength(definition.panelLength, { (millimeter) : [35, 55, 90] } as LengthBoundSpec);
        annotation { "Name" : "Panel thickness" }
        isLength(definition.panelThickness, { (millimeter) : [1.2, 1.6, 3] } as LengthBoundSpec);
        annotation { "Name" : "Wall thickness" }
        isLength(definition.wall, { (millimeter) : [1.6, 2.4, 4] } as LengthBoundSpec);
        annotation { "Name" : "Panel side clearance" }
        isLength(definition.clearance, { (millimeter) : [0.2, 0.35, 1] } as LengthBoundSpec);
        annotation { "Name" : "Minimum gross area ratio" }
        isReal(definition.areaRatio, { (unitless) : [0.65, 0.75, 1] } as RealBoundSpec);
        annotation { "Name" : "Boost fraction" }
        isReal(definition.boost, { (unitless) : [0, 0, 1] } as RealBoundSpec);
        annotation { "Name" : "Absolute angle ceiling" }
        isAngle(definition.angleCeiling, { (degree) : [0, 15, 20] } as AngleBoundSpec);
        annotation { "Name" : "Hinge plane Y" }
        isLength(definition.y, { (millimeter) : [0, 90, 150] } as LengthBoundSpec);
    }
    {
        const w = definition.width;
        const h = definition.height;
        const l = definition.panelLength;
        const t = definition.panelThickness;
        const wall = definition.wall;
        const gap = definition.clearance;
        const y = definition.y;
        const extra = 0.4 * millimeter;
        const sineMax = h * (1 - definition.areaRatio) / (2 * l);
        if (sineMax > 1 || definition.nozzleLength < l + 8 * millimeter)
            throw regenError("Nozzle must be at least 8 mm longer than panels; check constriction geometry.", ["nozzleLength", "panelLength", "areaRatio"]);
        const thetaMax = asin(sineMax);
        if (thetaMax > definition.angleCeiling)
            throw regenError("Required closure exceeds the angle ceiling. Increase minimum area or panel length.", ["areaRatio", "angleCeiling", "panelLength"]);
        const theta = thetaMax * definition.boost;
        const start = y - 5 * millimeter;
        const end = start + definition.nozzleLength;
        fCuboid(context, id + "frame", {
            "corner1" : vector(-w / 2 - wall, start, -h / 2 - wall - t - extra),
            "corner2" : vector(w / 2 + wall, end, h / 2 + wall + t + extra) });
        fCuboid(context, id + "passage", {
            "corner1" : vector(-w / 2, start - millimeter, -h / 2),
            "corner2" : vector(w / 2, end + millimeter, h / 2) });
        opBoolean(context, id + "passageCut", { "targets" : qCreatedBy(id + "frame", EntityType.BODY),
            "tools" : qCreatedBy(id + "passage", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        for (var i = 0; i < 2; i += 1)
        {
            const sign = i == 0 ? 1 : -1;
            const z = sign * h / 2;
            const pid = id + ("panel" ~ i);
            const sid = id + ("panelSpace" ~ i);
            fCuboid(context, sid, {
                "corner1" : vector(-w / 2 + gap - 0.1 * millimeter, y - 3.5 * millimeter, z - t - extra),
                "corner2" : vector(w / 2 - gap + 0.1 * millimeter, y + l + 3.5 * millimeter, z + t + extra) });
            opBoolean(context, id + ("panelSpaceCut" ~ i), { "targets" : qCreatedBy(id + "frame", EntityType.BODY),
                "tools" : qCreatedBy(sid, EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
            fCuboid(context, pid, {
                "corner1" : vector(-w / 2 + gap, y, sign == 1 ? z : z - t),
                "corner2" : vector(w / 2 - gap, y + l, sign == 1 ? z + t : z) });
            opTransform(context, id + ("closePanel" ~ i), { "bodies" : qCreatedBy(pid, EntityType.BODY),
                "transform" : rotationAround(line(vector(0 * millimeter, y, z), vector(1, 0, 0)), -sign * theta) });
            setProperty(context, { "entities" : qCreatedBy(pid, EntityType.BODY), "propertyType" : PropertyType.NAME,
                "value" : (i == 0 ? "Upper" : "Lower") ~ " boost panel - aerodynamic study" });
        }
        setProperty(context, { "entities" : qCreatedBy(id + "frame", EntityType.BODY), "propertyType" : PropertyType.NAME,
            "value" : "Integral nozzle section - aerodynamic study" });
    });

annotation { "Feature Type Name" : "Windflow radial straightener" }
export const windflowStraightener = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Duct diameter" }
        isLength(definition.diameter, { (millimeter) : [80, 114, 160] } as LengthBoundSpec);
        annotation { "Name" : "Radial clearance" }
        isLength(definition.clearance, { (millimeter) : [0.15, 0.3, 1] } as LengthBoundSpec);
        annotation { "Name" : "Vane count" }
        isInteger(definition.count, { (unitless) : [3, 7, 13] } as IntegerBoundSpec);
        annotation { "Name" : "Vane thickness" }
        isLength(definition.thickness, { (millimeter) : [0.8, 0.8, 2] } as LengthBoundSpec);
        annotation { "Name" : "Axial length" }
        isLength(definition.length, { (millimeter) : [8, 18, 35] } as LengthBoundSpec);
        annotation { "Name" : "Leading plane Y" }
        isLength(definition.y, { (millimeter) : [0, 42, 100] } as LengthBoundSpec);
    }
    {
        const ro = definition.diameter / 2 - definition.clearance;
        const ri = ro - 1.2 * millimeter;
        const y = definition.y;
        fCylinder(context, id + "ringOuter", { "bottomCenter" : vector(0 * millimeter, y, 0 * millimeter),
            "topCenter" : vector(0 * millimeter, y + definition.length, 0 * millimeter), "radius" : ro });
        fCylinder(context, id + "ringInner", { "bottomCenter" : vector(0 * millimeter, y, 0 * millimeter),
            "topCenter" : vector(0 * millimeter, y + definition.length, 0 * millimeter), "radius" : ri });
        opBoolean(context, id + "ringCut", { "targets" : qCreatedBy(id + "ringOuter", EntityType.BODY),
            "tools" : qCreatedBy(id + "ringInner", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        fCylinder(context, id + "hub", { "bottomCenter" : vector(0 * millimeter, y, 0 * millimeter),
            "topCenter" : vector(0 * millimeter, y + definition.length, 0 * millimeter), "radius" : 7 * millimeter });
        var all = [qCreatedBy(id + "ringOuter", EntityType.BODY), qCreatedBy(id + "hub", EntityType.BODY)];
        for (var i = 0; i < definition.count; i += 1)
        {
            const vaneId = id + ("vane" ~ i);
            fCuboid(context, vaneId, { "corner1" : vector(6.3 * millimeter, y, -definition.thickness / 2),
                "corner2" : vector(ro, y + definition.length, definition.thickness / 2) });
            opTransform(context, id + ("rotate" ~ i), { "bodies" : qCreatedBy(vaneId, EntityType.BODY),
                "transform" : rotationAround(line(vector(0, 0, 0) * millimeter, vector(0, 1, 0)), i * 360 * degree / definition.count) });
            all = append(all, qCreatedBy(vaneId, EntityType.BODY));
        }
        opBoolean(context, id + "join", { "tools" : qUnion(all), "operationType" : BooleanOperationType.UNION });
        fCylinder(context, id + "hubHole", { "bottomCenter" : vector(0 * millimeter, y, 0 * millimeter),
            "topCenter" : vector(0 * millimeter, y + definition.length, 0 * millimeter), "radius" : 5 * millimeter });
        opBoolean(context, id + "hubCut", { "targets" : qCreatedBy(id + "ringOuter", EntityType.BODY),
            "tools" : qCreatedBy(id + "hubHole", EntityType.BODY), "operationType" : BooleanOperationType.SUBTRACTION });
        setProperty(context, { "entities" : qCreatedBy(id + "ringOuter", EntityType.BODY),
            "propertyType" : PropertyType.NAME, "value" : "Radial straightener - comparison insert" });
    });
