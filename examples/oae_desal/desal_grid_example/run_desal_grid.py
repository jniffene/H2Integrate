from contextlib import chdir
from pathlib import Path

from h2integrate import H2IntegrateModel


def main():
    example_dir = Path(__file__).resolve().parent
    config = {
        "name": "H2Integrate_config",
        "system_summary": "Reverse-osmosis desalination supplied by grid electricity",
        "driver_config": str(example_dir / "driver_config.yaml"),
        "technology_config": str(example_dir / "tech_config.yaml"),
        "plant_config": str(example_dir / "plant_config.yaml"),
    }

    with chdir(example_dir):
        model = H2IntegrateModel(config)
        model.run()
        model.post_process()


if __name__ == "__main__":
    main()
