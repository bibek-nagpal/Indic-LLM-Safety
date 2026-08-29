# seeds/

Optional manually-validated EN/RH seed pairs per category. The
generator can be primed with up to 3 seed examples from here (via
`spec.seed_examples`) to anchor naturalness of the Romanized Hindi
register.

The repo intentionally ships **no** seed pairs by default. Seeds are
maintained in a separate, access-controlled corpus and loaded into the
category spec by the user before running.

To add seeds, edit the category YAML (e.g. `configs/categories/violence.yaml`)
and populate `seed_examples` like:

```yaml
seed_examples:
  - english: "..."
    romanized_hindi: "..."
    strategy: "Cls3LA"
    notes: "human-validated borderline pair"
```
