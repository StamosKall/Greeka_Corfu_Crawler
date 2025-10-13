# Initialize renv for the project
if (!require(renv, quietly = TRUE)) {
  install.packages("renv", repos = "https://cloud.r-project.org")
}

library(renv)

# Initialize renv
renv::init(bare = TRUE)

cat("✅ renv initialized successfully\n")