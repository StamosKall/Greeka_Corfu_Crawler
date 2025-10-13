# Install required R packages for Corfu Hotels Analysis
# Using renv for dependency management

library(renv)

# Set CRAN mirror
options(repos = c(CRAN = "https://cloud.r-project.org"))

cat("📦 Installing required packages for Corfu Hotels Analysis...\n\n")

# Only the packages we actually need (no database drivers)
packages <- c(
  # Data manipulation
  "jsonlite",
  "dplyr",

  # Spatial analysis
  "sf",
  "lwgeom",

  # OpenStreetMap data
  "osmdata",

  # Visualization
  "ggplot2",
  "RColorBrewer",
  "scales",
  "viridis"
)

# Install packages one by one to handle errors gracefully
installed_count <- 0
failed_packages <- c()

for (pkg in packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat(sprintf("Installing %s...\n", pkg))
    tryCatch({
      renv::install(pkg, prompt = FALSE)
      cat(sprintf("✅ %s installed successfully\n", pkg))
      installed_count <- installed_count + 1
    }, error = function(e) {
      cat(sprintf("❌ Failed to install %s: %s\n", pkg, e$message))
      failed_packages <- c(failed_packages, pkg)
    })
  } else {
    cat(sprintf("✅ %s already installed\n", pkg))
    installed_count <- installed_count + 1
  }
}

cat("\n" , rep("=", 50), "\n")
cat(sprintf("Installation Summary: %d/%d packages successful\n",
            installed_count, length(packages)))

if (length(failed_packages) > 0) {
  cat("\n⚠️  Failed packages:", paste(failed_packages, collapse = ", "), "\n")
}

# Take a snapshot of the installed packages
if (installed_count > 0) {
  cat("\n📸 Creating renv snapshot...\n")
  tryCatch({
    renv::snapshot(prompt = FALSE)
    cat("✅ Snapshot created successfully\n")
  }, error = function(e) {
    cat("⚠️  Snapshot creation failed:", e$message, "\n")
  })
}

cat("\n📋 Installed package versions:\n")
for (pkg in packages) {
  if (require(pkg, character.only = TRUE, quietly = TRUE)) {
    version <- packageVersion(pkg)
    cat(sprintf("  ✓ %s: %s\n", pkg, version))
  } else {
    cat(sprintf("  ✗ %s: NOT INSTALLED\n", pkg))
  }
}

cat("\n💡 To restore this environment later, run: renv::restore()\n")
cat("💡 To use this environment, run: renv::activate()\n")