// Publica o site no GitHub Pages: gera a versão final com a base /site-quakdo/ e envia a pasta dist
// para a branch gh-pages do repositório. Uso: npm run publicar
// O site fica em https://rodrigokelux.github.io/site-quakdo/
import { execSync } from "node:child_process";
import { mkdtempSync, cpSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const corre = (cmd, cwd) => execSync(cmd, { cwd, stdio: "inherit", env: { ...process.env, BASE: "/site-quakdo/", MSYS_NO_PATHCONV: "1" } });
const remoto = execSync("git remote get-url origin").toString().trim();
const quem = (k) => execSync(`git config ${k}`).toString().trim();
const commit = execSync("git rev-parse --short HEAD").toString().trim();

corre("npx vite build");
const pasta = mkdtempSync(join(tmpdir(), "quakdo-pages-"));
cpSync("dist", pasta, { recursive: true });
writeFileSync(join(pasta, ".nojekyll"), ""); // o GitHub Pages serve os ficheiros tal como estão
corre("git init -q -b gh-pages", pasta);
corre("git add -A", pasta);
corre(`git -c user.name="${quem("user.name")}" -c user.email="${quem("user.email")}" commit -q -m "Publicar o site (${commit})"`, pasta);
corre(`git push -q -f ${remoto} gh-pages`, pasta);
rmSync(pasta, { recursive: true, force: true });
console.log("Publicado: https://rodrigokelux.github.io/site-quakdo/");
