# Map Styling and Visualization Utilities
# ========================================
# Shared functions for consistent map styling
# Author: Reorganized from multiple R scripts
# Date: 2025

# Color palettes for walking times
get_walking_colors <- function(style = "default") {
  palettes <- list(
    default = c(
      "5" = "#E8F5E8",   # Very light green
      "10" = "#C8E6C9",  # Light green
      "15" = "#A5D6A7",  # Medium light green
      "20" = "#B9F6CA",  # Light teal
      "30" = "#81C784",  # Medium green
      "45" = "#66BB6A",  # Darker green
      "60" = "#4CAF50"   # Dark green
    ),
    gradient = c(
      "5" = "#1a9850",   # Dark Green
      "10" = "#66bd63",  # Medium Green
      "15" = "#a6d96a",  # Light Green
      "20" = "#d9ef8b",  # Yellow Green
      "30" = "#fee08b",  # Light Orange
      "45" = "#fdae61",  # Orange
      "60" = "#f46d43"   # Red Orange
    ),
    blue = c(
      "5" = "#E3F2FD",   # Very light blue
      "10" = "#BBDEFB",  # Light blue
      "15" = "#90CAF9",  # Medium light blue
      "20" = "#64B5F6",  # Medium blue
      "30" = "#42A5F5",  # Darker blue
      "45" = "#2196F3",  # Blue
      "60" = "#1976D2"   # Dark blue
    )
  )

  if (style %in% names(palettes)) {
    return(palettes[[style]])
  } else {
    return(palettes$default)
  }
}

# Get color for star rating
get_star_color <- function(star_rating, style = "default") {
  palettes <- list(
    default = c(
      "5" = "#FFD700",  # Gold
      "4" = "#FFA500",  # Orange
      "3" = "#32CD32",  # Lime Green
      "2" = "#4169E1",  # Royal Blue
      "1" = "#808080",  # Gray
      "NA" = "#C0C0C0"  # Silver
    ),
    heat = c(
      "5" = "#d73027",  # Red
      "4" = "#fc8d59",  # Orange
      "3" = "#fee08b",  # Yellow
      "2" = "#d9ef8b",  # Light green
      "1" = "#91bfdb",  # Light blue
      "NA" = "#999999"  # Gray
    )
  )

  palette <- if (style %in% names(palettes)) palettes[[style]] else palettes$default

  rating_str <- if (is.na(star_rating)) "NA" else as.character(star_rating)
  if (rating_str %in% names(palette)) {
    return(palette[rating_str])
  } else {
    return(palette["NA"])
  }
}

# Create base map theme
create_base_theme <- function(title_size = 16, subtitle_size = 12,
                            legend_position = "bottom") {
  ggplot2::theme_void() +
    ggplot2::theme(
      plot.title = ggplot2::element_text(size = title_size, hjust = 0.5,
                                         face = "bold", color = "darkblue"),
      plot.subtitle = ggplot2::element_text(size = subtitle_size, hjust = 0.5,
                                            color = "gray40"),
      plot.caption = ggplot2::element_text(size = 10, hjust = 0.5,
                                           color = "gray50", margin = ggplot2::margin(t = 10)),
      legend.position = legend_position,
      legend.title = ggplot2::element_text(size = 12, face = "bold"),
      legend.text = ggplot2::element_text(size = 10),
      legend.key.size = ggplot2::unit(0.8, "cm"),
      panel.background = ggplot2::element_rect(fill = "#f0f8ff", color = NA),
      plot.background = ggplot2::element_rect(fill = "white", color = NA),
      plot.margin = ggplot2::margin(20, 20, 20, 20)
    )
}

# Create isochrone map
create_isochrone_map <- function(hotels_sf, isochrones_sf, corfu_boundary = NULL,
                               title = "Walking Distance Isochrones for Corfu Hotels",
                               subtitle = NULL, color_style = "default") {

  # Get color palette
  walking_colors <- get_walking_colors(color_style)

  # Calculate subtitle if not provided
  if (is.null(subtitle)) {
    subtitle <- sprintf("Analysis of %d Hotels with %d Walking Zones",
                       nrow(hotels_sf), nrow(isochrones_sf))
  }

  # Start with base plot
  p <- ggplot2::ggplot() + create_base_theme()

  # Add Corfu boundary if available
  if (!is.null(corfu_boundary)) {
    p <- p + ggplot2::geom_sf(data = corfu_boundary,
                              fill = "#f5f5f5",
                              color = "#cccccc",
                              size = 0.5,
                              alpha = 0.3)
  }

  # Add isochrones (largest to smallest)
  time_intervals <- sort(unique(isochrones_sf$time_min), decreasing = TRUE)

  for (time_min in time_intervals) {
    isochrones_subset <- isochrones_sf[isochrones_sf$time_min == time_min, ]

    if (nrow(isochrones_subset) > 0) {
      time_str <- as.character(time_min)
      fill_color <- if (time_str %in% names(walking_colors)) {
        walking_colors[time_str]
      } else {
        "#CCCCCC"
      }

      p <- p + ggplot2::geom_sf(data = isochrones_subset,
                                fill = fill_color,
                                color = fill_color,
                                alpha = 0.6,
                                size = 0.2)
    }
  }

  # Add hotel points
  p <- p + ggplot2::geom_sf(data = hotels_sf,
                           color = "darkred",
                           fill = "red",
                           size = 1.5,
                           alpha = 0.8,
                           shape = 21,
                           stroke = 0.5)

  # Add labels
  p <- p + ggplot2::labs(
    title = title,
    subtitle = subtitle,
    caption = paste("Generated on", Sys.Date(),
                   "• Walking Speed: 5 km/h • Data: OpenStreetMap")
  )

  # Set coordinate limits
  bbox <- sf::st_bbox(hotels_sf)
  padding <- 0.05
  p <- p + ggplot2::coord_sf(
    xlim = c(bbox["xmin"] - padding, bbox["xmax"] + padding),
    ylim = c(bbox["ymin"] - padding, bbox["ymax"] + padding),
    expand = FALSE
  )

  return(p)
}

# Add legend for walking times
add_walking_legend <- function(plot, time_intervals, color_style = "default") {
  walking_colors <- get_walking_colors(color_style)

  legend_data <- data.frame(
    time = factor(time_intervals, levels = time_intervals),
    color = walking_colors[as.character(time_intervals)],
    label = paste(time_intervals, "min walk")
  )

  plot + ggplot2::scale_fill_manual(
    name = "Walking Time Zones",
    values = stats::setNames(legend_data$color, legend_data$label),
    labels = legend_data$label,
    guide = ggplot2::guide_legend(
      title.position = "top",
      override.aes = list(alpha = 0.7, size = 3)
    )
  )
}

# Create statistics box for map
create_stats_box <- function(hotels_data, position = "bottomleft") {
  stats_text <- paste(
    sprintf("Total Hotels: %d", nrow(hotels_data)),
    sprintf("With Coordinates: %d", sum(!is.na(hotels_data$lat))),
    sprintf("With Ratings: %d", sum(!is.na(hotels_data$star_rating))),
    sep = "\n"
  )

  # Position mapping
  positions <- list(
    bottomleft = c(0.05, 0.05),
    bottomright = c(0.95, 0.05),
    topleft = c(0.05, 0.95),
    topright = c(0.95, 0.95)
  )

  pos <- if (position %in% names(positions)) positions[[position]] else positions$bottomleft

  ggplot2::annotation_custom(
    grob = grid::textGrob(stats_text,
                          x = pos[1], y = pos[2],
                          just = c("left", "bottom"),
                          gp = grid::gpar(col = "darkblue",
                                        fontsize = 10,
                                        fontface = "bold"))
  )
}

# Save map with high quality
save_map <- function(plot, filename, width = 16, height = 12, dpi = 300) {
  cat(sprintf("💾 Saving map as: %s\n", filename))

  ggplot2::ggsave(
    filename = filename,
    plot = plot,
    width = width,
    height = height,
    dpi = dpi,
    units = "in",
    bg = "white"
  )

  cat(sprintf("✅ Map saved successfully (%d x %d inches at %d DPI)\n",
              width, height, dpi))
}

# Create a simple legend data frame
create_legend_df <- function(time_intervals, color_style = "default") {
  walking_colors <- get_walking_colors(color_style)

  data.frame(
    time = time_intervals,
    color = walking_colors[as.character(time_intervals)],
    label = paste(time_intervals, "minutes"),
    stringsAsFactors = FALSE
  )
}

# Add scale bar to map
add_scale_bar <- function(plot, location = "bottomright", width_km = 5) {
  # This is a placeholder - actual implementation would require
  # ggspatial package or similar for proper scale bars
  plot
}