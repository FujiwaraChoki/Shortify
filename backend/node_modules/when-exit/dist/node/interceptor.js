/* IMPORT */
import process from 'node:process';
import Signals from './signals.js';
/* MAIN */
class Interceptor {
    /* CONSTRUCTOR */
    constructor() {
        /* VARIABLES */
        this.callbacks = new Set();
        this.exited = false;
        /* API */
        this.exit = (signal) => {
            if (this.exited)
                return;
            this.exited = true;
            for (const callback of this.callbacks) {
                callback();
            }
            if (signal) {
                process.kill(process.pid, signal);
            }
        };
        this.hook = () => {
            process.once('exit', () => this.exit());
            for (const signal of Signals) {
                process.once(signal, () => this.exit(signal));
            }
        };
        this.register = (callback) => {
            this.callbacks.add(callback);
            return () => {
                this.callbacks.delete(callback);
            };
        };
        this.hook();
    }
}
/* EXPORT */
export default new Interceptor();
