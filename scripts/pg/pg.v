module main

import os

fn create_error(message string, is_fatal bool) {
  println("[ERROR] ${message}")
  if is_fatal {
    exit(1)
  }
}

fn get_file_extension(filename string) string {
  slices := os.base(filename).split(".")
  return slices[slices.len - 1]
}

struct DirectoryIgnore {
  patterns []string
}

fn get_lines(files []string) (int, map[string]int) {
  mut total_lines, mut lines := 0, map[string]int{}
  for file in files {
    content := os.read_lines(file) or {
      create_error(err.msg, false)
      continue
    }
    total_lines += content.len
    extension := get_file_extension(file)
    lines[extension] += content.len
  }
  return total_lines, lines
}

fn get_files(files []string) map[string]int {
  mut extensions := map[string]int{}
  for file in files {
    extension := get_file_extension(file)
    extensions[extension] += 1
  }
  return extensions
}

fn (ignore DirectoryIgnore) ignore_dir(dir string) bool {
  return ignore.patterns.map(it == dir).len > 0
}

fn find_gitignore(directory string) []string {
  filename := os.join_path_single(directory, ".gitignore")
  if os.is_file(filename) {
    content := os.read_lines(filename) or {
      return []
    }
    return content.filter(fn (line string) bool {
      return line.trim_space().len > 0 && line[line.len-1] == `/`
    }).map(it.trim_space().trim("/"))
  } else {
    return []
  }
}

fn walk(directory string, _ignore DirectoryIgnore) []string {
  mut files := []string{}
  content := os.ls(directory) or {
    create_error(err.msg, true)
    return files
  }
  for filename in content {
    if filename == '.git' && os.is_dir(filename) { continue }
    path := os.join_path_single(directory, filename)
    if os.is_dir(path) {
      if _ignore.ignore_dir(filename) { continue }
      files << walk(path, _ignore)
    } else {
      files << path
    }
  }
  return files
}

fn get_directory(args []string) string {
  if args.len > 0 {
    directory := args[0]
    if !os.is_dir(directory) {
      create_error("${directory} doesn't exist", true)
    }
    return directory
  }
  return os.getwd()
}

fn main() {
  args := os.args[1..]
  directory := get_directory(args)

  gitignore_patterns := find_gitignore(directory)
  mut ignore := DirectoryIgnore{gitignore_patterns}

  files := walk(directory, ignore)

  loc, lines := get_lines(files)
  file_count := get_files(files)
  println("Extension:Lines(${loc}):Files(${files.len})")
  for ext in lines.keys() {
    curr_lines := lines[ext]
    println("${ext} - ${curr_lines} - ${file_count[ext]}")
  }
}
