# Contributing Guidelines

If you would like to contribute to our codebase, here is how you can do so!

## Branching Strategy

Our project maintains two main branches:  
- **`main`**: The stable release branch.  
- **`development`**: The active development branch where new features are integrated.  

When adding a feature:  
1. Create a new branch specific to your feature.  
2. Merge your feature branch into the `development` branch.  
3. After review, changes from `development` will be merged into `main` if deemed valuable.  

---

## Making Changes  

If you'd like to contribute, please follow these instructions.

### Fork and Clone  

1. [Fork this repo on GitHub](https://github.com/twitter/opensource-website/fork).  
2. Clone your fork:  

```bash
git clone https://github.com/$YOUR_USERNAME/opensource-website/
cd opensource-website
```

---

## Development Workflow  

1. Create a new branch for your feature:  

```bash
git checkout -b feature/your-feature-name
```  

2. Make your changes and commit them.  

3. Push your feature branch to your fork:  

```bash
git push origin feature/your-feature-name
```  

4. Merge your branch into `development` on your fork:  

```bash
git checkout development
git merge feature/your-feature-name
git push origin development
```  

---

## Pull Requests  

Pull requests should remain focused in scope and avoid containing unrelated commits.  

1. [Open a Pull Request](http://help.github.com/send-pull-requests/) with a clear title and description, targeting `development`.  

2. Your changes will be reviewed, tested, and merged into `main` if approved.  

