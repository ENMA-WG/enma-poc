import numpy as np
import ifcopenshell
import ifcopenshell.geom


IFC_FILE = r"data/営繕BIMモデル_EM.ifc"

TARGETS = [
    "3TIe45XffAO8vSs7ykYfD4",  # Round, inferred D=150
    "2Bsml8mET6dOcU05ZdRiPy",  # Rect, inferred 750 x 637.63
    "2Bsml8mET6dOcU05ZdRiPS",  # Rect, inferred 600 x 400
    "2Bsml8mET6dOcU05ZdRiPV",  # Rect, inferred 450 x 3.76
]


def get_bbox(element, settings):
    shape = ifcopenshell.geom.create_shape(settings, element)

    verts = np.array(shape.geometry.verts, dtype=float).reshape(-1, 3)

    minimum = verts.min(axis=0)
    maximum = verts.max(axis=0)
    size = maximum - minimum

    return minimum, maximum, size


def main():
    model = ifcopenshell.open(IFC_FILE)

    settings = ifcopenshell.geom.settings()

    print("=== DUCT GEOMETRY INSPECTION ===")

    for global_id in TARGETS:
        element = model.by_guid(global_id)

        print()
        print("=" * 70)
        print("GlobalId   :", element.GlobalId)
        print("Name       :", element.Name)
        print("ObjectType :", element.ObjectType)

        try:
            minimum, maximum, size = get_bbox(element, settings)

            print(
                "BBox min   : "
                f"X={minimum[0]:.4f}, "
                f"Y={minimum[1]:.4f}, "
                f"Z={minimum[2]:.4f}"
            )

            print(
                "BBox max   : "
                f"X={maximum[0]:.4f}, "
                f"Y={maximum[1]:.4f}, "
                f"Z={maximum[2]:.4f}"
            )

            print(
                "BBox size  : "
                f"X={size[0]:.4f}, "
                f"Y={size[1]:.4f}, "
                f"Z={size[2]:.4f}"
            )

        except Exception as exc:
            print("GEOMETRY ERROR:", exc)


if __name__ == "__main__":
    main()