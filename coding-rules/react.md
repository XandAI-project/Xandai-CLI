# React Development Rules

## Project Structure
- Use `src/` for all source code
- Components in `src/components/`
- Pages/Views in `src/pages/`
- Utilities in `src/utils/`
- Assets in `src/assets/`

## Component Guidelines
- Use functional components with hooks
- Use TypeScript when possible
- Name components with PascalCase
- One component per file
- Use default exports for components

## State Management
- Use useState for local state
- Use useEffect for side effects
- Consider useContext for shared state
- Use useReducer for complex state logic

## Styling
- Use CSS Modules or styled-components
- Follow BEM methodology for CSS classes
- Mobile-first responsive design
- Use CSS variables for theming

## Performance
- Use React.memo for expensive components
- Implement lazy loading with React.lazy
- Optimize re-renders with useMemo and useCallback
- Use proper key props in lists

## Code Quality
- Use PropTypes or TypeScript for type checking
- Follow ESLint and Prettier configurations
- Write unit tests with React Testing Library
- Use semantic HTML elements

## File Naming
- Components: `ComponentName.jsx` or `ComponentName.tsx`
- Styles: `ComponentName.module.css`
- Tests: `ComponentName.test.jsx`
- Types: `types.ts` or `ComponentName.types.ts`

## Dependencies
- Prefer npm over yarn unless project requires yarn
- Keep dependencies updated
- Use exact versions for critical dependencies
- Separate devDependencies from dependencies
