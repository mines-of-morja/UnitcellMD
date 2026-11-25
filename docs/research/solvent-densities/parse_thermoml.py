import sys
import xml.etree.ElementTree as ET


def ln(e):
    return e.tag.split("}")[-1]


def kids(e, n):
    return [c for c in e.iter() if ln(c) == n]


def txt(e, n):
    k = kids(e, n)
    return k[0].text if k else None


for f in sys.argv[1:]:
    try:
        r = ET.parse(f).getroot()
    except ET.ParseError as ex:
        print(f.split("/")[-1], "not XML:", ex)
        continue
    print("=====", f.split("/")[-1], "|", txt(r, "sTitle"))
    names = {}
    for c in kids(r, "Compound"):
        names[txt(c, "nOrgNum")] = (txt(c, "sCommonName"), txt(c, "sFormulaMolec"))
    for p in kids(r, "PureOrMixtureData"):
        comps = [names.get(txt(c, "nOrgNum")) for c in p if ln(c) == "Component"]
        if len(comps) != 1:
            continue
        props = {}
        for q in [c for c in p if ln(c) == "Property"]:
            props[txt(q, "nPropNumber")] = (
                txt(q, "ePropName"),
                txt(q, "eMethodName") or txt(q, "sMethodName"),
            )
        var = {
            txt(v, "nVarNumber"): (
                txt(v, "eVarType")
                or (txt(v, "VariableType") and next(x.text for x in kids(v, "VariableType")[0]))
            )
            for v in p
            if ln(v) == "Variable"
        }
        cons = [
            (next(x.text for x in kids(v, "ConstraintType")[0]), txt(v, "nConstraintValue"))
            for v in p
            if ln(v) == "Constraint"
        ]
        for nv in [c for c in p if ln(c) == "NumValues"]:
            vs = [
                (var.get(txt(v, "nVarNumber")), txt(v, "nVarValue"))
                for v in nv
                if ln(v) == "VariableValue"
            ]
            for pv in [c for c in nv if ln(c) == "PropertyValue"]:
                pn = props.get(txt(pv, "nPropNumber"))
                if pn and any(k in pn[0] for k in ("density", "aporization", "Refractive")):
                    print(
                        "  ",
                        comps[0][0],
                        "|",
                        pn[0],
                        "|",
                        pn[1],
                        "|",
                        vs,
                        cons,
                        "=",
                        txt(pv, "nPropValue"),
                        "+-",
                        txt(pv, "nCombExpandUncertValue") or txt(pv, "nExpandUncertValue"),
                    )
