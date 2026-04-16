import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(__dirname, "..", "core", "domain_seed.json");

const rows = [
  ["\uC77C\uC790\u00B7\uC2DC\uAC04", "\uC77C\uC790", "DATE", null, null, "\uC77C\uC790DT", "\uC77C \uB2E8\uC704 \uB0A0\uC9DC"],
  ["\uC77C\uC790\u00B7\uC2DC\uAC04", "\uB0A0\uC9DC", "DATE", null, null, "\uB0A0\uC9DCDT", null],
  ["\uC77C\uC790\u00B7\uC2DC\uAC04", "\uC77C\uC2DC", "TIMESTAMP", null, null, "\uC77C\uC2DCTS", "\uD0C0\uC784\uC874 \uC5C6\uC74C \uC608\uC2DC"],
  ["\uC77C\uC790\u00B7\uC2DC\uAC04", "\uC2DC\uAC01", "TIME", null, null, "\uC2DC\uAC01TM", null],
  ["\uC2DD\uBCC4\u00B7\uD0A4", "ID", "VARCHAR", null, null, "IDVC50", "\uBB38\uC790 \uC2DD\uBCC4\uC790 \uAE30\uBCF8 \uAE38\uC774"],
  ["\uC2DD\uBCC4\u00B7\uD0A4", "ID", "INTEGER", null, null, "IDINT", "\uC815\uC218 \uD0A4"],
  ["\uC2DD\uBCC4\u00B7\uD0A4", "ID", "BIGINT", null, null, "IDBIG", "BIGINT \uD0A4"],
  ["\uCF54\uB4DC\u00B7\uBD84\uB958", "\uCF54\uB4DC", "VARCHAR", 20, null, "\uCF54\uB4DCVC20", null],
  ["\uCF54\uB4DC\u00B7\uBD84\uB958", "\uAD6C\uBD84", "VARCHAR", 10, null, "\uAD6C\uBD84VC10", null],
  ["\uCF54\uB4DC\u00B7\uBD84\uB958", "\uC720\uD615", "VARCHAR", 20, null, "\uC720\uD615VC20", null],
  ["\uCF54\uB4DC\u00B7\uBD84\uB958", "\uC0C1\uD0DC", "VARCHAR", 20, null, "\uC0C1\uD0DCVC20", null],
  ["\uCF54\uB4DC\u00B7\uBD84\uB958", "\uBC88\uD638", "VARCHAR", 30, null, "\uBC88\uD638VC30", null],
  ["\uCF54\uB4DC\u00B7\uBD84\uB958", "\uC77C\uB828\uBC88\uD638", "VARCHAR", 50, null, "\uC77C\uB828\uBC88\uD638VC50", null],
  ["\uCF54\uB4DC\u00B7\uBD84\uB958", "\uC21C\uBC88", "INTEGER", null, null, "\uC21C\uBC88INT", null],
  ["\uBA85\uCE6D\u00B7\uC124\uBA85", "\uBA85", "VARCHAR", 100, null, "\uBA85VC100", null],
  ["\uBA85\uCE6D\u00B7\uC124\uBA85", "\uBE44\uACE0", "VARCHAR", 500, null, "\uBE44\uACE0VC500", null],
  ["\uBA85\uCE6D\u00B7\uC124\uBA85", "\uC124\uBA85", "TEXT", null, null, "\uC124\uBA85TX", null],
  ["\uBA85\uCE6D\u00B7\uC124\uBA85", "\uB0B4\uC6A9", "TEXT", null, null, "\uB0B4\uC6A9TX", null],
  ["\uAE08\uC561\u00B7\uAE08\uC728", "\uAE08\uC561", "NUMERIC", null, null, "\uAE08\uC561NM18.2", "\uAC00\uACA9\u00B7\uBE44\uC6A9 \uACC4\uC5F4\uACFC \uB3D9\uC77C \uADC0\uCE59"],
  ["\uAE08\uC561\u00B7\uAE08\uC728", "\uAC00\uACA9", "NUMERIC", null, null, "\uAC00\uACA9NM18.2", null],
  ["\uAE08\uC561\u00B7\uAE08\uC728", "\uAC00\uC561", "NUMERIC", null, null, "\uAC00\uC561NM18.2", null],
  ["\uAE08\uC561\u00B7\uAE08\uC728", "\uBE44\uC6A9", "NUMERIC", null, null, "\uBE44\uC6A9NM18.2", null],
  ["\uAE08\uC561\u00B7\uAE08\uC728", "\uB2E8\uAC00", "NUMERIC", null, null, "\uB2E8\uAC00NM18.4", "\uB2E8\uAC00 \uC18C\uC218 \uC790\uB9AC"],
  ["\uC218\uB7C9\u00B7\uAC74\uC218", "\uC218\uB7C9", "NUMERIC", null, null, "\uC218\uB7C9NM15.3", null],
  ["\uC218\uB7C9\u00B7\uAC74\uC218", "\uAC74\uC218", "INTEGER", null, null, "\uAC74\uC218INT", null],
  ["\uC218\uB7C9\u00B7\uAC74\uC218", "\uD68F\uC218", "INTEGER", null, null, "\uD68F\uC218INT", null],
  ["\uC218\uB7C9\u00B7\uAC74\uC218", "\uB7C9", "NUMERIC", null, null, "\uB7C9NM15.3", null],
  ["\uC218\uB7C9\u00B7\uAC74\uC218", "\uC218", "NUMERIC", null, null, "\uC218NM15.3", null],
  ["\uC218\uB7C9\u00B7\uAC74\uC218", "\uAE30\uB85D", "NUMERIC", null, null, "\uAE30\uB85DNM15.3", null],
  ["\uBE44\uC728", "\uBE44\uC728", "NUMERIC", 5, 2, "\uBE44\uC728NM5.2", null],
  ["\uC5EC\uBD80", "\uC5EC\uBD80", "CHAR", 1, null, "\uC5EC\uBD80CH1", "Y/N \uB4F1"],
  ["\uC5F0\uB77D\u00B7\uC8FC\uC18C", "IP\uC8FC\uC18C", "VARCHAR", 45, null, "IP\uC8FC\uC18CVC45", "IPv6 \uB300\uBE44"],
  ["\uC5F0\uB77D\u00B7\uC8FC\uC18C", "\uC8FC\uC18C", "VARCHAR", 200, null, "\uC8FC\uC18CVC200", null],
  ["\uC5F0\uB77D\u00B7\uC8FC\uC18C", "\uC774\uBA54\uC77C", "VARCHAR", 100, null, "\uC774\uBA54\uC77CVC100", null],
  ["\uAD6C\uC870\uD654", "JSON", "JSONB", null, null, "JSONJB", "\uBC14\uC774\uB108\uB9AC JSON \uAD8C\uC7A5"],
  ["\uAD6C\uC870\uD654", "JSON", "JSON", null, null, "JSONJS", null],
  ["\uAD6C\uC870\uD654", "UUID", "UUID", null, null, "UUIDUID", "uuid-ossp \uB4F1"],
];

fs.writeFileSync(out, JSON.stringify(rows, null, 2), "utf8");
console.log("wrote", rows.length, "rows ->", out);
