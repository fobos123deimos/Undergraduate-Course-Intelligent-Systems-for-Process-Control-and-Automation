# Historical Blending Tank project

`Blending_Tank-main/` preserves the six files supplied from the owner's archived project, without changing their bytes. The original archive SHA-256 is `4f5fd03ce9d7d41cd88db429da5bc4b4f086bed40050a45d2bbfa1d9afa305cd`. The adjacent `checksums.json` records each extracted member.

The original README reads **Smart Systems: Blending Tank**. The Simulink models record R2015b and internal dates from 14 to 23 April 2022. Their relationship to the first homework is a chronology-based inference, not an identifier found in the files. Metadata labels are retained unchanged and do not independently establish academic authorship.

The physical state is `[X,V]`: solute mass fraction and volume. For constant density, perfect mixing and no reaction:

$$\dot V=\frac{w_1+w_2-w}{\rho},\qquad
\dot X=\frac{w_1(X_1-X)+w_2(X_2-X)}{\rho V}.$$

The source initializes `X=0`, `V=2`. It supplies the variables `w1,w2,w,x1,x2,p` as S-function parameters. The state-space diagram's visible input constants are 500, 200, 0.4, 0.75 and 650, in its own input ordering. The archive does not supply a complete initialization script that defines every parameter and its unit. Do not silently infer density from rounded matrix entries.

Points to resolve before using the old models as a numerical reference:

- Some source comments attach volume/temperature units to mass fraction or volume; the equations above use the physical definitions.
- Nonzero `w1+w2-w` implies changing volume. A fixed equilibrium volume cannot simultaneously satisfy that imbalance.
- The supplied concentration matrix has a negative sensitivity to the first low-concentration feed (`B(1,1)=-0.0000529`), while the corresponding transfer block displays a positive numerator. The files are preserved rather than silently reconciled.
- The old initialization interface and encoding require inspection in an appropriate MATLAB/Simulink installation. The copied binary models have not been executed in this environment.

The new [physical implementation](../../matlab/blending_rhs.m) derives the same balance independently and checks positive volume/density. Its explicit illustration uses `rho=1000 kg/m3`, inlet mass flows 500 and 200, outlet 700, inlet mass fractions 0.4 and 0.75, and volume 2 m3. Those documented defaults close the mass balance; they are not claimed as parameters recovered from the archive. The new course's dimensionless concentration experiments use a separate, fully stated normalization.
