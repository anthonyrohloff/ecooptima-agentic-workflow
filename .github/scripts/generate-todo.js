// .github/scripts/generate-todo.js
const fs = require("fs");
const path = require("path");
const core = require("@actions/core");
const github = require("@actions/github");

async function run() {
  try {
    const token = process.env.GITHUB_TOKEN;
    if (!token) {
      throw new Error("GITHUB_TOKEN is not set");
    }

    const octokit = github.getOctokit(token);
    const { owner, repo } = github.context.repo;

    // Fetch all open issues (excluding PRs)
    let issues = [];
    let page = 1;

    while (true) {
      const { data } = await octokit.rest.issues.listForRepo({
        owner,
        repo,
        state: "open",
        per_page: 100,
        page,
      });

      if (data.length === 0) break;

      issues = issues.concat(
        data.filter((issue) => !issue.pull_request) // ignore PRs
      );
      page += 1;
    }

    // Group issues by label name
    const groups = {};

    for (const issue of issues) {
      // If an issue has no labels, put it under "unlabeled"
      const labels = issue.labels.length
        ? issue.labels.map((l) => (typeof l === "string" ? l : l.name))
        : ["unlabeled"];

      for (const label of labels) {
        const labelName = label || "unlabeled";
        if (!groups[labelName]) {
          groups[labelName] = [];
        }
        groups[labelName].push(issue);
      }
    }

    // Build TODO.md content
    let content = "# TODO\n\nGenerated from open GitHub issues.\n\n";

    const sortedLabelNames = Object.keys(groups).sort((a, b) =>
      a.localeCompare(b)
    );

    for (const labelName of sortedLabelNames) {
      content += `## ${labelName}\n\n`;
      const issuesForLabel = groups[labelName].sort(
        (a, b) => a.number - b.number
      );

      for (const issue of issuesForLabel) {
        const title = issue.title.replace(/\r?\n/g, " ");
        const body = (issue.body || "").trim();

        content += `- [#${issue.number}] ${title}\n`;
        if (body) {
          // indent body for readability
          const indented = body
            .split(/\r?\n/)
            .map((line) => `  ${line}`)
            .join("\n");
          content += `${indented}\n`;
        }
        content += "\n";
      }
    }

    const todoPath = path.join(process.cwd(), "TODO.md");
    fs.writeFileSync(todoPath, content, "utf8");
    console.log("TODO.md updated.");

  } catch (error) {
    core.setFailed(error.message);
  }
}

run();
