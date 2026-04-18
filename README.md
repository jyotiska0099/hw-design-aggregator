# hw-design-aggregator
Python pipeline that ingests ARM CMSIS-SVD hardware register-map XML files, builds a typed in-memory data model (Pydantic dataclasses) representing peripheral definitions and register maps, and auto-generates three output artifacts: a C header file with \texttt{\#define} macros, a Markdown traceability report, and a JSON summary
